from config.mistral_client import call_mistral


def analyze_budget(from_city, to_city, budget, days, nights, transport):
    prompt = f"""
You are an intelligent travel budget advisor.

Trip Details:
From: {from_city}
To: {to_city}
Duration: {days} days, {nights} nights
Transport: {transport}
User Budget: ₹{budget}

TASK:
- Analyze whether this budget is sufficient for the trip
- Clearly state if the budget is LOW, ADEQUATE, or HIGH
- If budget is low, suggest a realistic minimum required budget
- Suggest cost-saving tips if budget is low
- If budget is adequate, confirm feasibility
- If budget is high, suggest possible upgrades
- Respond like a human travel planner
- Plain text only
"""

    return call_mistral(prompt)
