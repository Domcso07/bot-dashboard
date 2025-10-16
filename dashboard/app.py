import os
import json
import threading
import requests
from flask import Flask, redirect, request, session, render_template
import disnake
from disnake.ext import commands

import json

CONFIG_FILE = "config.json"

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_prefix(bot, message):
    config = load_config()
    guild_id = str(message.guild.id) if message.guild else "default"
    return config.get(guild_id, {}).get("prefix", "!")


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---- Discord bot ----
intents = disnake.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot bejelentkezett: {bot.user}")

@bot.command()
async def hello(ctx):
    """Hello parancs: üdvözlés és prefix figyelembevétele"""
    config = load_config()
    guild_id = str(ctx.guild.id)
    settings = config.get(guild_id, {})
    
    welcome = settings.get("welcome")
    
    if welcome:
        await ctx.send(welcome)
    else:
        await ctx.send(f"Szia {ctx.author.name}! Ez a szerver prefixe: `{get_prefix(bot, ctx.message)}`")

@bot.command()
async def test_welcome(ctx, member: disnake.Member = None):
    """
    Szimulálja az üdvözlő üzenetet.
    Ha nincs member megadva, a parancsot használó személyt veszi.
    """
    member = member or ctx.author
    config = load_config()
    guild_id = str(ctx.guild.id)
    settings = config.get(guild_id, {})
    
    message = settings.get("welcome_message")
    channel_id = settings.get("welcome_channel")
    
    if not message:
        await ctx.send("❌ Nincs beállítva üdvözlő üzenet!")
        return
    
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(message.replace("{user}", member.mention))
            await ctx.send(f"✅ Üdvözlő üzenet elküldve a {channel.name} csatornába!")
            return
    
    # Ha nincs csatorna beállítva, küldje ide
    await ctx.send(message.replace("{user}", member.mention))


# ---- Flask dashboard ----
app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = "1424398378632216697"
CLIENT_SECRET = "GxEO_JVsJg-arexpNTiwmsggLUoqwKxS"
REDIRECT_URI = "http://localhost:8080/callback"
API_ENDPOINT = "https://discord.com/api"

# ----- JSON config kezelése -----
def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----- BOT -----
def get_prefix(bot, message):
    config = load_config()
    guild_id = str(message.guild.id) if message.guild else "default"
    return config.get(guild_id, {}).get("prefix", "!")

intents = disnake.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot bejelentkezve: {bot.user}")

@bot.event
async def on_member_join(member):
    config = load_config()
    guild_id = str(member.guild.id)
    settings = config.get(guild_id, {})
    message = settings.get("welcome_message")
    channel_id = settings.get("welcome_channel")

    if not message:
        return  # nincs üzenet, kilépünk

    # channel_id átalakítása int-re, ha van
    channel = None
    if channel_id:
        try:
            channel = member.guild.get_channel(int(channel_id))
        except ValueError:
            channel = None

    # ha nincs csatorna beállítva vagy nem található, használjuk a system_channel-t
    if not channel:
        channel = member.guild.system_channel

    if channel:
        await channel.send(message.replace("{user}", member.mention))


@bot.command()
async def hello(ctx):
    config = load_config()
    guild_id = str(ctx.guild.id)
    message = config.get(guild_id, {}).get("welcome_message", f"Szia {ctx.author.name}!")
    await ctx.send(message)

@bot.command()
async def test_welcome(ctx, member: disnake.Member = None):
    member = member or ctx.author
    config = load_config()
    guild_id = str(ctx.guild.id)
    settings = config.get(guild_id, {})
    message = settings.get("welcome_message")
    channel_id = settings.get("welcome_channel")
    if not message:
        await ctx.send("❌ Nincs beállítva üdvözlő üzenet!")
        return
    channel = ctx.guild.get_channel(channel_id) if channel_id else ctx.channel
    await channel.send(message.replace("{user}", member.mention))
    await ctx.send(f"✅ Üdvözlő üzenet elküldve!")

# ----- FLASK DASHBOARD -----
app = Flask(__name__)
app.secret_key = "valami_jo_secret"

@app.route("/")
def index():
    if "token" in session:
        return redirect("/dashboard")
    return render_template("login.html")

@app.route("/login")
def login():
    return redirect(f"{API_ENDPOINT}/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify guilds",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
    response.raise_for_status()
    tokens = response.json()
    session["token"] = tokens["access_token"]
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    if "token" not in session:
        return redirect("/login")
    headers = {"Authorization": f"Bearer {session['token']}"}
    user = requests.get(f"{API_ENDPOINT}/users/@me", headers=headers).json()
    guilds = requests.get(f"{API_ENDPOINT}/users/@me/guilds", headers=headers).json()
    bot_guilds = [g for g in guilds if any(bg.id == int(g["id"]) for bg in bot.guilds)]
    return render_template("dashboard.html", user=user, guilds=bot_guilds)

@app.route("/settings/<guild_id>", methods=["GET", "POST"])
def settings(guild_id):
    if "token" not in session:
        return redirect("/login")
    headers = {"Authorization": f"Bearer {session['token']}"}
    guild = requests.get(f"{API_ENDPOINT}/guilds/{guild_id}", headers=headers).json()
    config = load_config()

    if request.method == "POST":
        config[guild_id]["prefix"] = request.form.get("prefix", "!")
        config[guild_id]["welcome_message"] = request.form.get("welcome", "")
        config[guild_id]["welcome_channel"] = int(request.form.get("channel")) if request.form.get("channel") else None
        config[guild_id]["auto_role"] = int(request.form.get("autorole")) if request.form.get("autorole") else None
        config[guild_id]["mod_log_channel"] = int(request.form.get("modlog")) if request.form.get("modlog") else None
        config[guild_id]["embed_color"] = request.form.get("embedcolor", "#00FF00")
        save_config(config)

    settings_data = config.get(guild_id, {
    "prefix": "!",
    "welcome_message": "",
    "welcome_channel": None,
    "auto_role": None,
    "mod_log_channel": None,
    "embed_color": "#00FF00"
    })
    return render_template("settings.html", guild=guild, **settings_data, saved=(request.method=="POST"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ----- FUTTATÁS -----
def run_flask():
    app.run(host="0.0.0.0", port=8080, debug=False)  # debug=False, így nem lesz signal hiba

threading.Thread(target=run_flask).start()
bot.run("MTQyNDM5ODM3ODYzMjIxNjY5Nw.G2gwNs.mOQUQbEY8wzSgYAvwbZZSFrCVsMcUYIthq0xis")
