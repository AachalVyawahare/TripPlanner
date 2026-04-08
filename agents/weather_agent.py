import requests
from config.weather_config import WEATHER_API_KEY, WEATHER_API_URL
from config.mistral_client import call_mistral


def get_weather(city):
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(WEATHER_API_URL, params=params)
        data = response.json()

        if response.status_code != 200:
            return "Weather information not available."

        # Raw live data
        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]

        # -------- Agentic Reasoning via LLM --------
        prompt = f"""
You are an intelligent travel weather advisor.

Live Weather Data:
City: {city}
Temperature: {temperature}°C
Feels Like: {feels_like}°C
Humidity: {humidity}%
Condition: {description}

TASK:
- Analyze whether this weather is comfortable for travel
- Clearly state if it is comfortable or uncomfortable
- Suggest the best weather or season to visit this place
- If someone travels in current conditions, give practical precautions
- Reason like a human travel expert, not using fixed rules
- Plain text only
"""

        analysis = call_mistral(prompt)

        weather_report = f"""
WEATHER ANALYSIS FOR {city}

Current Conditions:
Temperature: {temperature}°C
Feels Like: {feels_like}°C
Humidity: {humidity}%
Condition: {description}

Agent Analysis:
{analysis}
"""

        return weather_report.strip()

    except Exception:
        return "Error fetching weather data."