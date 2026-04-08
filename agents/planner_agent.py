from agent_loop import agent_loop
from utils.text_cleaner import clean_text


def planner(user_data):
    print("Agentic Planner started...\n")

    memory = agent_loop(user_data)

    return {
        "budget":       clean_text(str(memory.get("budget",      "Budget information not available."))),
        "weather":      clean_text(str(memory.get("weather",     "Weather information not available."))),
        "destinations": clean_text(str(memory.get("destination", "Destination information not available."))),
        "hotels":       clean_text(str(memory.get("hotel",       "Hotel information not available."))),
        "transport":    clean_text(str(memory.get("transport",   "Transport information not available."))),
        "day_plan":     clean_text(str(memory.get("day_plan",    "Day plan not available."))),
        "reflection":   clean_text(str(memory.get("reflection",  "Plan review not available.")))
    }