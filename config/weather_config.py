import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY not found. Please set it in .env file.")