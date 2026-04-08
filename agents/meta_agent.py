from config.mistral_client import call_mistral


def meta_agent(world_state):
    """
    TRUE Agentic Meta-Agent:
    Uses LLM reasoning to dynamically decide which agent
    should run next based on current world state and memory.
    """

    done = world_state["done"]
    goal = world_state["goal"]
    memory = world_state["memory"]

    # All tasks completed
    all_tasks = {"destination", "weather", "hotel", "budget", "transport", "day_plan"}
    if all_tasks.issubset(set(done.keys())):
        return "stop"

    # Build a summary of what's been done so far
    completed = list(done.keys()) if done else ["nothing yet"]

    # Summarize memory so far for context
    memory_summary = {}
    for key, val in memory.items():
        if val:
            memory_summary[key] = str(val)[:300]

    prompt = f"""
You are an intelligent AI orchestrator managing a travel planning system.

Trip Details:
- From: {goal['from_city']}
- To: {goal['to_city']}
- Budget: Rs.{goal['budget']}
- Days: {goal['days']}, Nights: {goal['nights']}
- Transport: {goal['transport']}

Already completed tasks: {completed}
Remaining tasks: {list(all_tasks - set(done.keys()))}

Summary of results so far:
{memory_summary}

DECISION RULES:
- Always start with 'destination' if not done
- Then do 'weather'
- Then do 'hotel'
- Then do 'budget'
- Then do 'transport'
- Then do 'day_plan' (MUST run after destination and weather are both done)
- day_plan builds the hour-by-hour schedule using destination and weather info
- If all tasks are done, say 'stop'

Reply with ONLY one single word from this list:
destination, weather, hotel, budget, transport, day_plan, stop

Your decision:
"""

    try:
        response = call_mistral(prompt).strip().lower()

        valid_actions = {"destination", "weather", "hotel", "budget", "transport", "day_plan", "stop"}

        # Extract first word only in case LLM adds extra text
        first_word = response.split()[0] if response.split() else ""

        if first_word in valid_actions:
            # Don't repeat already done tasks
            if first_word in done and first_word != "stop":
                return _fallback_next(done)
            return first_word

        return _fallback_next(done)

    except Exception as e:
        print(f"Meta-agent LLM error: {e}")
        return _fallback_next(done)


def _fallback_next(done):
    """
    Fallback sequential order if LLM fails or gives invalid response.
    """
    default_order = ["destination", "weather", "hotel", "budget", "transport", "day_plan"]
    for task in default_order:
        if task not in done:
            return task
    return "stop"