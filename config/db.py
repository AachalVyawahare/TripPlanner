from pymongo import MongoClient

# 🔹 Replace YOUR_PASSWORD with your actual Atlas password
MONGO_URI = "YOUR_MONGO_URI"

client = MongoClient(MONGO_URI)

db = client["trip_planner"]

users_collection = db["users"]
history_collection = db["trip_history"]
