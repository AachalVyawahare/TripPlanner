# from werkzeug.security import generate_password_hash, check_password_hash
# from config.db import users_collection

# def create_user(name, email, password):
#     hashed_password = generate_password_hash(password)

#     user = {
#         "name": name,
#         "email": email,
#         "password": hashed_password
#     }

#     users_collection.insert_one(user)

# def find_user_by_email(email):
#     return users_collection.find_one({"email": email})

# def verify_password(stored_password, provided_password):
#     return check_password_hash(stored_password, provided_password)

from werkzeug.security import generate_password_hash, check_password_hash
from config.db import users_collection


def create_user(name, email, password):
    hashed_password = generate_password_hash(password)
    user = {
        "name":     name,
        "email":    email,
        "password": hashed_password
    }
    users_collection.insert_one(user)


def find_user_by_email(email):
    return users_collection.find_one({"email": email})


def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)


def update_user_info(old_email, new_name, new_email):
    """Update name and/or email. Returns True if successful."""
    # Check if new email is taken by someone else
    if new_email != old_email:
        existing = users_collection.find_one({"email": new_email})
        if existing:
            return False, "This email is already used by another account."

    users_collection.update_one(
        {"email": old_email},
        {"$set": {"name": new_name, "email": new_email}}
    )
    return True, "Profile updated successfully!"


def update_user_password(email, current_password, new_password):
    """Verify current password then update to new one. Returns (True/False, message)."""
    user = find_user_by_email(email)
    if not user:
        return False, "User not found."

    if not check_password_hash(user["password"], current_password):
        return False, "Current password is incorrect."

    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."

    hashed = generate_password_hash(new_password)
    users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed}}
    )
    return True, "Password changed successfully!"