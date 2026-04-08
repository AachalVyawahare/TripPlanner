"""
Agent Loop Module

This module coordinates multiple AI agents to generate a complete travel plan.
It manages execution flow, real-time status updates, and error handling.
"""
# Local agent modules
from agents.meta_agent import meta_agent
from agents.destination_agent import get_destinations
from agents.weather_agent import get_weather
from agents.hotel_agent import get_hotels
from agents.transport_agent import get_transport
from agents.budget_agent import analyze_budget
from agents.reflection_agent import reflection_agent
from agents.day_planner_agent import get_day_plan
logging.basicConfig(level=logging.INFO)
# ============================================
# GLOBAL REAL-TIME STATUS LIST
# Frontend SSE reads from this live
# ============================================
from threading import Lock

agent_status = []
status_lock = Lock()


def push_status(msg):
    logging.info(f"[STATUS] {msg}")
    with status_lock:
        agent_status.append(msg)


def run_agent(action, world_state):
    """
    Executes a specific agent based on the action.

    Args:
        action (str): Agent type (destination, weather, etc.)
        world_state (dict): Current state of planning

    Returns:
        result from agent or fallback message
    """
    data = world_state.get("goal", {})

    try:

        if action == "destination":
            push_status(f"📍 Discovering places to visit in {data['to_city']}...")
            result = get_destinations(
                f"From {data['from_city']} to {data['to_city']}, "
                f"duration {data['days']} days, {data['nights']} nights, "
                f"budget Rs.{data['budget']}, preferences: {data.get('extra', 'general')}"
            )

        elif action == "weather":
            push_status(f"🌤 Checking live weather conditions in {data['to_city']}...")
            result = get_weather(data["to_city"])

        elif action == "hotel":
            push_status(f"🏨 Searching budget hotels in {data['to_city']}...")
            result = get_hotels(
                data["to_city"],
                data["budget"],
                data["nights"]
            )

        elif action == "transport":
            push_status(f"🚆 Planning {data['transport']} route from {data['from_city']} to {data['to_city']}...")
            result = get_transport(
                data["from_city"],
                data["to_city"],
                data["transport"]
            )

        elif action == "budget":
            push_status(f"💰 Analyzing your ₹{data['budget']} budget for this trip...")
            result = analyze_budget(
                data["from_city"],
                data["to_city"],
                data["budget"],
                data["days"],
                data["nights"],
                data["transport"]
            )

        elif action == "day_plan":
            push_status(f"🗓 Building your day-by-day itinerary for {data['days']} days...")
            result = get_day_plan(
                to_city=data["to_city"],
                days=data["days"],
                destinations_text=world_state["memory"].get("destination", ""),
                weather_text=world_state["memory"].get("weather", ""),
                extra=data.get("extra", "")
            )

        else:
            return "No valid action provided."

        # Validate result
        if result is None or result == "":
            return f"{action.title()} information unavailable."

        if isinstance(result, str) and ("api error" in result.lower() or "quota exceeded" in result.lower()):
            return f"{action.title()} agent encountered an API issue. Please try again."

        push_status(f"✅ {action.title()} info ready!")
        return result

    except Exception as e:
        print(f"[ERROR] Reflection agent failed: {e}")
        logging.error(f"Agent '{action}' failed: {e}")
        logging.error(f"Reflection agent failed: {e}")
        return f"{action.title()} information is currently unavailable. Please verify manually."


def agent_loop(user_data):
    """
    Main orchestrator for agent-based travel planning.

    Uses meta-agent to decide sequence of execution,
    collects outputs, and performs final reflection.

    Args:
        user_data (dict): User input data

    Returns:
        dict: Final aggregated travel plan
    """

    # Clear previous status on each new run
    global agent_status
    agent_status.clear()

    world_state = {
        "goal": user_data,
        "done": {},
        "memory": {}
    }

    push_status(f"🤖 Agentic AI started planning your trip to {user_data['to_city']}...")

    max_iterations = 12
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        push_status("🧠 Meta-agent is deciding next step...")
        action = meta_agent(world_state)

        if action == "stop":
            push_status("✅ All agents completed. Preparing your plan...")
            break

        result = run_agent(action, world_state)

        world_state["memory"][action] = result
        world_state["done"][action] = True

    # Reflection Agent
    push_status("🔍 Reflection agent is reviewing your complete plan...")
    try:
        reflection_result = reflection_agent(world_state["memory"])
        world_state["memory"]["reflection"] = reflection_result
        push_status("✨ Plan review complete! Loading your results...")
    except Exception as e:
        print(f"[ERROR] Reflection agent failed: {e}")
        world_state["memory"]["reflection"] = "Plan review could not be completed."
        push_status("⚠️ Review skipped. Loading your results...")

    push_status("DONE")
    return world_state["memory"]