from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)

db = client["botdb"]
settings = db["settings"]

@app.route("/settings", methods=["POST"])
def save_settings():
    data = request.json
    guild_id = data["guild_id"]
    prefix = data["prefix"]

    settings.update_one(
        {"guild_id": guild_id},
        {"$set": {"prefix": prefix}},
        upsert=True
    )

    return jsonify({"status": "ok"})

@app.route("/settings/<guild_id>", methods=["GET"])
def get_settings(guild_id):
    result = settings.find_one({"guild_id": guild_id})
    if not result:
        return jsonify({"prefix": "!"})
    return jsonify({"prefix": result["prefix"]})

@app.route("/")
def home():
    return "Backend működik"
