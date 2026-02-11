from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

# -----------------------------
# FLASK + CORS
# -----------------------------
app = Flask(__name__)
CORS(app)  # fontos a dashboard miatt!

# -----------------------------
# MONGO KAPCSOLAT
# -----------------------------
client = MongoClient(os.getenv("MONGO_URL"))
db = client["botdb"]

servers_col = db["servers"]
roles_col = db["roles"]
settings_col = db["settings"]


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return "Dashboard backend működik."


# -----------------------------
# BOT → BACKEND: SZERVERLISTA
# -----------------------------
@app.route("/update_servers", methods=["POST"])
def update_servers():
    servers = request.json["servers"]  # [{id, name}]
    servers_col.delete_many({})
    servers_col.insert_many(servers)
    return jsonify({"status": "ok"})


# -----------------------------
# BOT → BACKEND: RANGLISTA
# -----------------------------
@app.route("/update_roles", methods=["POST"])
def update_roles():
    guild_id = request.json["guild_id"]
    roles = request.json["roles"]  # [{id, name}]

    roles_col.update_one(
        {"guild_id": guild_id},
        {"$set": {"roles": roles}},
        upsert=True
    )
    return jsonify({"status": "ok"})


# -----------------------------
# DASHBOARD → BACKEND: SZERVERLISTA LEKÉRÉSE
# -----------------------------
@app.route("/servers", methods=["GET"])
def get_servers():
    servers = list(servers_col.find({}, {"_id": 0}))
    return jsonify(servers)


# -----------------------------
# DASHBOARD → BACKEND: RANGLISTA LEKÉRÉSE
# -----------------------------
@app.route("/roles/<guild_id>", methods=["GET"])
def get_roles(guild_id):
    doc = roles_col.find_one({"guild_id": guild_id}, {"_id": 0})
    if not doc:
        return jsonify([])
    return jsonify(doc["roles"])


# -----------------------------
# DASHBOARD → BACKEND: BEÁLLÍTÁSOK LEKÉRÉSE
# -----------------------------
@app.route("/settings/<guild_id>", methods=["GET"])
def get_settings(guild_id):
    doc = settings_col.find_one({"guild_id": guild_id}, {"_id": 0})

    if not doc:
        # alapértelmezett értékek
        return jsonify({
            "warn_allowed_roles": [],
            "warn_dm": True,
            "rang_approve_roles": []
        })

    return jsonify(doc)


# -----------------------------
# DASHBOARD → BACKEND: BEÁLLÍTÁSOK MENTÉSE
# -----------------------------
@app.route("/settings", methods=["POST"])
def save_settings():
    data = request.json
    guild_id = data["guild_id"]

    # csak azt mentjük, ami érkezett
    update_data = {}

    if "warn_allowed_roles" in data:
        update_data["warn_allowed_roles"] = data["warn_allowed_roles"]

    if "warn_dm" in data:
        update_data["warn_dm"] = data["warn_dm"]

    if "rang_approve_roles" in data:
        update_data["rang_approve_roles"] = data["rang_approve_roles"]

    settings_col.update_one(
        {"guild_id": guild_id},
        {"$set": update_data},
        upsert=True
    )

    return jsonify({"status": "ok"})


# -----------------------------
# FUTTATÁS
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
