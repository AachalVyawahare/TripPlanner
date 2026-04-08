import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

MODEL_NAME = "mistral-small"

if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found. Please set it in .env file.")