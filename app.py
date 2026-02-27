from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
import os

app = Flask(__name__)
CORS(app)

MONGO = MongoClient(os.getenv("MONGO_URL"))
db = MONGO["botdb"]

servers_col = db["servers"]
roles_col = db["roles"]
settings_col = db["settings"]

BOT_URL = os.getenv("BOT_URL")  # pl. https://your-bot.onrender.com


@app.route("/")
def home():
    return "Dashboard backend működik."


# BOT → BACKEND: szerverlista
@app.route("/update_servers", methods=["POST"])
def update_servers():
    servers = request.json["servers"]
    servers_col.delete_many({})
    servers_col.insert_many(servers)
    return jsonify({"status": "ok"})


# BOT → BACKEND: ranglista
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


# DASHBOARD → BACKEND: szerverlista
@app.route("/servers", methods=["GET"])
def get_servers():
    return jsonify(list(servers_col.find({}, {"_id": 0})))


# DASHBOARD → BACKEND: ranglista
@app.route("/roles/<guild_id>", methods=["GET"])
def get_roles(guild_id):
    doc = roles_col.find_one({"guild_id": guild_id}, {"_id": 0})
    return jsonify(doc["roles"] if doc else [])


# DASHBOARD → BACKEND: csatornalista (BOT-tól kérjük)
@app.route("/channels/<guild_id>", methods=["GET"])
def get_channels(guild_id):
    try:
        r = requests.get(f"{BOT_URL}/channels/{guild_id}")
        return jsonify(r.json())
    except:
        return jsonify([])


# DASHBOARD → BACKEND: beállítások lekérése
@app.route("/settings/<guild_id>", methods=["GET"])
def get_settings(guild_id):
    doc = settings_col.find_one({"guild_id": guild_id}, {"_id": 0})

    if not doc:
        return jsonify({
            "warn_allowed_roles": [],
            "warn_dm": True,
            "warn_log_enabled": True,
            "warn_log_channel_id": None,
            "warn_panel_required": True,
            "warn_panel_channel_id": None
        })

    doc.setdefault("warn_allowed_roles", [])
    doc.setdefault("warn_dm", True)
    doc.setdefault("warn_log_enabled", True)
    doc.setdefault("warn_log_channel_id", None)
    doc.setdefault("warn_panel_required", True)
    doc.setdefault("warn_panel_channel_id", None)

    return jsonify(doc)


# DASHBOARD → BACKEND: beállítások mentése
@app.route("/settings", methods=["POST"])
def save_settings():
    data = request.json
    guild_id = data["guild_id"]

    settings_col.update_one(
        {"guild_id": guild_id},
        {"$set": data},
        upsert=True
    )

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
