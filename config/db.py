from pymongo import MongoClient

# 🔹 Replace YOUR_PASSWORD with your actual Atlas password
MONGO_URI = "mongodb+srv://trip_admin:kiFB2TnNFb0q212T@tripplannercluster.rxnqay4.mongodb.net/trip_planner?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["trip_planner"]

users_collection = db["users"]
history_collection = db["trip_history"]