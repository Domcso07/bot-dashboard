from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # <<< EZ OLDJA MEG A HIBÁT

client = MongoClient(os.getenv("MONGO_URL"))
db = client["botdb"]
servers_col = db["servers"]
roles_col = db["roles"]
settings_col = db["settings"]


@app.route("/")
def home():
    return "Backend működik"


@app.route("/update_servers", methods=["POST"])
def update_servers():
    servers = request.json["servers"]
    servers_col.delete_many({})
    servers_col.insert_many(servers)
    return jsonify({"status": "ok"})


@app.route("/update_roles", methods=["POST"])
def update_roles():
    guild_id = request.json["guild_id"]
    roles = request.json["roles"]
    roles_col.update_one(
        {"guild_id": guild_id},
        {"$set": {"roles": roles}},
        upsert=True
    )
    return jsonify({"status": "ok"})


@app.route("/servers", methods=["GET"])
def get_servers():
    servers = list(servers_col.find({}, {"_id": 0}))
    return jsonify(servers)


@app.route("/roles/<guild_id>", methods=["GET"])
def get_roles(guild_id):
    doc = roles_col.find_one({"guild_id": guild_id}, {"_id": 0})
    if not doc:
        return jsonify([])
    return jsonify(doc["roles"])


@app.route("/settings/<guild_id>", methods=["GET"])
def get_settings(guild_id):
    doc = settings_col.find_one({"guild_id": guild_id}, {"_id": 0})
    if not doc:
        return jsonify({
            "warn_allowed_roles": []
        })
    return jsonify(doc)


@app.route("/settings", methods=["POST"])
def save_settings():
    data = request.json
    guild_id = data["guild_id"]

    settings_col.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "warn_allowed_roles": data.get("warn_allowed_roles", [])
        }},
        upsert=True
    )

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
