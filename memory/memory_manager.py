import json
import os

MEMORY_FILE = "memory/user_memory.json"


def save_user_memory(user_data):
    """Save user input into JSON memory file"""

    # If file does not exist, create it
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w") as f:
            json.dump([], f)

    # Load existing memory
    with open(MEMORY_FILE, "r") as f:
        data = json.load(f)

    # Append new user input
    data.append(user_data)

    # Save back to file
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_user_memory():
    """Read stored memory"""

    if not os.path.exists(MEMORY_FILE):
        return []

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)
