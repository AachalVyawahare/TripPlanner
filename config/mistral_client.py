import requests
from config.mistral_config import MISTRAL_API_KEY, MISTRAL_API_URL, MODEL_NAME


def call_mistral(prompt):
    """
    Sends a prompt to Mistral AI and returns the response.
    """

    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY is not set in environment variables")

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            MISTRAL_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        return f"Request failed: {str(e)}"

    if response.status_code != 200:
        return "Mistral API error or quota exceeded."

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return "Invalid response from Mistral API."