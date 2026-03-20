import nextcord
from nextcord.ext import commands, app_commands
import flask
import os
import time
import threading
import asyncio
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN env var required!")
    exit(1)

GUILD_ID = 1289789596238086194
ALLOWED_ROLE_IDS = [1470596832794251408, 1470596825575854223, 1470596818298601567]
WELCOME_CHANNEL_ID = 1470597378116681812

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='>', intents=intents)
bot.tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync(guild=nextcord.Object(id=GUILD_ID))
        logger.info(f'{bot.user} logged in! Synced {len(synced)} commands.')
    except Exception as e:
        logger.error(f'Sync failed: {e}')
    activity = nextcord.Activity(type=nextcord.ActivityType.watching, name="Liberty County | /say")
    await bot.change_presence(activity=activity, status=nextcord.Status.online)
    bot.start_time = time.time()

@bot.tree.command(guild=nextcord.Object(id=GUILD_ID), name="say", description="Say message as bot (admin)")
async def say(interaction: nextcord.Interaction, message: str):
    if not any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("No permission!", ephemeral=True)
        return
    await interaction.response.defer()
    await interaction.channel.send(message)
    await interaction.delete_original_response()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"Welcome {member.mention}!")

# Flask for Render
app = flask.Flask(__name__)

@app.route('/')
def home():
    return {"status": "alive"}

@app.route('/status')
def status():
    uptime = time.time() - getattr(bot, 'start_time', 0)
    return {
        "flask": True,
        "bot_ready": bot.is_ready(),
        "guilds": len(bot.guilds),
        "uptime": uptime
    }

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.run(bot.start(BOT_TOKEN))
