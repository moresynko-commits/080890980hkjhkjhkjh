import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import flask
import os
import time
import threading
import asyncio
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# Config - token required, others hardcoded
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN env var required!")

GUILD_ID = 1289789596238086194
ALLOWED_ROLE_IDS = [1470596832794251408, 1470596825575854223, 1470596818298601567]
WELCOME_CHANNEL_ID = 1470597378116681812

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='>', intents=intents, sync_commands=True)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has logged in! Connected to {len(bot.guilds)} guilds.')
    activity = nextcord.Activity(type=nextcord.ActivityType.watching, name="Liberty County | /say")
    await bot.change_presence(activity=activity, status=nextcord.Status.online)
    logger.info("Bot ready! Slash commands auto-synced.")

@bot.slash_command(guild_ids=[GUILD_ID], description='Say a message as the bot (admin only)')
async def say(interaction: Interaction, message: str):
    if not any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ No permission!", ephemeral=True)
        return
    await interaction.response.defer()
    await interaction.channel.send(message)
    await interaction.delete_original_response()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"Welcome {member.mention} to Liberty County State Roleplay!")

# Simple Flask app for health checks (Render)
app = flask.Flask(__name__)

@app.route('/')
def home():
    return {'status': 'alive', 'service': 'LCSRPC Simplified Bot'}

@app.route('/status')
def status():
    uptime = time.time() - bot_start_time if 'bot_start_time' in globals() else 0
    ready = bot.is_ready() if hasattr(bot, 'is_ready') else False
    return {
        'flask_alive': True,
        'bot_ready': ready,
        'guilds': len(bot.guilds),
        'uptime_s': uptime
    }

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f'Starting Flask on port {port}')
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    global bot_start_time
    bot_start_time = time.time()
    
    # Start Flask in daemon thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run bot
    try:
        asyncio.run(bot.start(BOT_TOKEN))
    except KeyboardInterrupt:
        logger.info('Shutting down...')
    finally:
        if not bot.is_closed():
            asyncio.run(bot.close())
