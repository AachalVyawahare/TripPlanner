from config.mistral_client import call_mistral

def get_hotels(location, budget=5000, nights=1):
    max_per_night = budget // nights

    prompt = f"""
    You are a local hotel planner.

    Location: {location}
    Nights: {nights}
    Maximum price per night: {max_per_night} INR

    RULES:
    - Only budget hotels or lodges
    - Price must be below limit
    - Plain text only
    - No luxury hotels

    Suggest 2 or 3 options.
    """

    return call_mistral(prompt)
