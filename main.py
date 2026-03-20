import nextcord
from nextcord.ext import commands
import flask
import os
import threading
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN required!")
    exit(1)

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='>', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} logged in! Guilds: {len(bot.guilds)}')
    activity = nextcord.Activity(name="Liberty County State | dsc.gg/lcsrpc", type=nextcord.ActivityType.watching)
    await bot.change_presence(activity=activity)

@bot.command()
async def say(ctx, *, message):
    # Simple role check - hardcoded admin roles
    allowed_roles = [1470596832794251408, 1470596825575854223, 1470596818298601567]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.send("No permission!", delete_after=5)
    await ctx.message.delete()
    await ctx.send(message)

@bot.event
async def on_member_join(member):
    guild = member.guild
    channel_id = 1470597378116681812
    channel = bot.get_channel(channel_id)
    if channel:
        human_count = len([m for m in guild.members if not m.bot])
        ordinal = 'st' if human_count % 10 == 1 and human_count % 100 != 11 else 'nd' if human_count % 10 == 2 and human_count % 100 != 12 else 'rd' if human_count % 10 == 3 and human_count % 100 != 13 else 'th'
        emoji_badge = '<:Welcome0:1484564259395604572><:Welcome1:1484564289309380780><:Welcome2:1484564315888681000><:Welcome3:1484564376995234037>'
        msg = f"{emoji_badge} ** to Liberty County State Roleplay Community (LCSRPC), {member.mention}.** You are our `{human_count}{ordinal}` member. > Thanks for joining, and have a wonderful day!"
        await channel.send(msg)

app = flask.Flask(__name__)

@app.route('/')
def home():
    return {"status": "alive", "bot": str(bot.user) if bot.is_ready() else "starting"}

@app.route('/status')
def status():
    return {
        "flask": True,
        "bot_ready": bot.is_ready(),
        "guilds": len(bot.guilds),
        "latency": bot.latency if bot.is_ready() else 0
    }

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.run(bot.start(BOT_TOKEN))
