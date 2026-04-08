# Standard libraries
import os
import time
import json
from datetime import datetime

# Third-party
import requests
from flask import (
    Flask, render_template, request,
    redirect, session, flash, Response,
    stream_with_context, jsonify
)

# Local modules
from agents.planner_agent import planner
from memory.memory_manager import save_user_memory
from models.user_model import (
    create_user, find_user_by_email, verify_password,
    update_user_info, update_user_password
)
from utils.pdf_email_service import generate_pdf, send_email_with_pdf
from config.db import history_collection
from config.mistral_config import MISTRAL_API_KEY, MISTRAL_API_URL, MODEL_NAME

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")


# =====================================================
# SPELL CORRECT CITY NAME USING MISTRAL
# =====================================================
def correct_city_name(city_name):
    try:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": [{
                "role": "user",
                "content": (
                    f"Correct this Indian city or place name if the spelling is wrong. "
                    f"Return ONLY the corrected name, nothing else, no explanation: '{city_name}'"
                )
            }],
            "temperature": 0.0,
            "max_tokens": 20
        }
        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            return city_name
        corrected = response.json()["choices"][0]["message"]["content"].strip()
        return corrected if corrected else city_name
    except Exception:
        return city_name


# =====================================================
# AUTH CHECK
# =====================================================
def login_required():
    return "user" in session


# =====================================================
# SSE — REAL-TIME STATUS STREAM
# =====================================================
@app.route("/stream-status")
def stream_status():
    def generate():
        from agent_loop import agent_status
        last_index = 0
        timeout = 120
        elapsed = 0
        while elapsed < timeout:
            current_len = len(agent_status)
            if last_index < current_len:
                for i in range(last_index, current_len):
                    msg = agent_status[i]
                    yield f"data: {json.dumps(msg)}\n\n"
                    if msg == "DONE":
                        return
                last_index = current_len
            time.sleep(0.4)
            elapsed += 0.4
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# =====================================================
# HOME / TRIP PLANNER
# =====================================================
@app.route("/", methods=["GET", "POST"])
def index():
    if not login_required():
        return redirect("/login")

    if request.method == "POST":
        try:
            budget = int(request.form["budget"])
            days   = int(request.form["days"])
            nights = int(request.form["nights"])
        except ValueError:
            flash("Budget, days and nights must be valid numbers.", "danger")
            return redirect("/")

        if budget <= 0 or days <= 0 or nights <= 0:
            flash("Budget, days and nights must be greater than zero.", "danger")
            return redirect("/")

        raw_from = request.form["from_city"].strip()
        raw_to   = request.form["to_city"].strip()

        if not raw_from or not raw_to:
            flash("Please enter both From City and Destination City.", "danger")
            return redirect("/")

        from_city = correct_city_name(raw_from)
        to_city   = correct_city_name(raw_to)

        user_data = {
            "from_city": from_city,
            "to_city":   to_city,
            "budget":    budget,
            "days":      days,
            "nights":    nights,
            "transport": request.form["transport"],
            "extra":     request.form.get("extra", "").strip()
        }

        save_user_memory(user_data)
        result = planner(user_data)

        history_collection.insert_one({
            "user_email": session["user"]["email"],
            "from_city":  user_data["from_city"],
            "to_city":    user_data["to_city"],
            "budget":     user_data["budget"],
            "days":       user_data["days"],
            "nights":     user_data["nights"],
            "transport":  user_data["transport"],
            "created_at": datetime.now(),
            "full_plan": {
                "budget":       result["budget"],
                "weather":      result["weather"],
                "destinations": result["destinations"],
                "hotels":       result["hotels"],
                "transport":    result["transport"],
                "day_plan":     result["day_plan"],
                "reflection":   result["reflection"]
            }
        })

        return render_template(
            "result.html",
            budget=result["budget"],
            weather=result["weather"],
            destinations=result["destinations"],
            hotels=result["hotels"],
            transport=result["transport"],
            day_plan=result["day_plan"],
            reflection=result["reflection"],
            to_city=user_data["to_city"],
            from_city=user_data["from_city"],
            transport_mode=user_data["transport"],
            days=user_data["days"]
        )

    return render_template("index.html")


# =====================================================
# EDIT PROFILE
# =====================================================
@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    if not login_required():
        return redirect("/login")

    if request.method == "POST":
        action = request.form.get("action")

        # ── Update name / email ──
        if action == "update_info":
            new_name  = request.form.get("name", "").strip()
            new_email = request.form.get("email", "").strip()

            if not new_name or not new_email:
                flash("Name and email cannot be empty.", "danger")
                return redirect("/edit-profile")

            success, message = update_user_info(
                old_email=session["user"]["email"],
                new_name=new_name,
                new_email=new_email
            )

            if success:
                # Update session with new values
                session["user"]["name"]  = new_name
                session["user"]["email"] = new_email
                session.modified = True
                flash(message, "success")
            else:
                flash(message, "danger")

            return redirect("/edit-profile")

        # ── Change password ──
        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password     = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect("/edit-profile")

            success, message = update_user_password(
                email=session["user"]["email"],
                current_password=current_password,
                new_password=new_password
            )

            flash(message, "success" if success else "danger")
            return redirect("/edit-profile")

    return render_template("edit_profile.html")


# =====================================================
# REGISTER
# =====================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form["name"]
        email    = request.form["email"]
        password = request.form["password"]
        if find_user_by_email(email):
            flash("User already exists. Please login.", "warning")
            return redirect("/login")
        create_user(name, email, password)
        flash("Registration successful. Please login.", "success")
        return redirect("/login")
    return render_template("register.html")


# =====================================================
# LOGIN
# =====================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form["email"]
        password = request.form["password"]
        user     = find_user_by_email(email)
        if not user:
            flash("You don't have an account. Please register first.", "warning")
            return redirect("/login")
        if not verify_password(user["password"], password):
            flash("Incorrect password. Please try again.", "danger")
            return redirect("/login")
        session["user"] = {"name": user["name"], "email": user["email"]}
        return redirect("/")
    return render_template("login.html")


# =====================================================
# LOGOUT
# =====================================================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# =====================================================
# SEND PDF
# =====================================================
@app.route("/send-pdf", methods=["POST"])
def send_pdf():
    if not login_required():
        return redirect("/login")

    full_plan   = request.form["full_plan"]
    extra_email = request.form.get("extra_email", "").strip()
    to_city     = request.form.get("to_city", "").strip()
    user_email  = session["user"]["email"]

    pdf_file = generate_pdf(full_plan, to_city)

    try:
        send_email_with_pdf(user_email, pdf_file)
        if extra_email:
            send_email_with_pdf(extra_email, pdf_file)
        message = "✅ PDF sent successfully to your email!"
        status  = "success"
    except Exception as e:
       import logging
        logging.error(f"Email error: {e}") 
        message = "❌ Error sending email. Please check your connection."
        status  = "error"
    finally:
        if os.path.exists(pdf_file):
            os.remove(pdf_file)

    return jsonify({"status": status, "message": message})


# =====================================================
# DELETE TRIP
# =====================================================
@app.route("/delete-trip", methods=["POST"])
def delete_trip():
    if not login_required():
        return jsonify({"status": "error", "message": "Not logged in"})
    try:
        from bson import ObjectId
        from bson.errors import InvalidId

        data    = request.get_json()
        trip_id = data.get("trip_id", "").strip()

        try:
            oid = ObjectId(trip_id)
        except InvalidId as e:
            return jsonify({"status": "error", "message": f"Invalid ID: {trip_id}"})

        result = history_collection.delete_one({
            "_id":        oid,
            "user_email": session["user"]["email"]
        })

        if result.deleted_count == 1:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Trip not found"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# =====================================================
# HISTORY
# =====================================================
@app.route("/history")
def history():
    if not login_required():
        return redirect("/login")
    user_email = session["user"]["email"]
    trips = list(
        history_collection.find({"user_email": user_email}).sort("created_at", -1)
    )
    return render_template("history.html", trips=trips)


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True, threaded=True)