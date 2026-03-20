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
    channel = bot.get_channel(1470941203343216843)
    if channel:
        await channel.send(member.mention)

        # Image Embed 1
        embed1 = nextcord.Embed(color=0xffffff)
        embed1.set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484676770224410775/alrwelc.png?ex=69bf187d&is=69bdc6fd&hm=93aa43677dac68a2b37ac68dc12d7f151c4d45cdf9a7f976df3e9e88b17022d1&")

        # Text Embed 2
        embed2 = nextcord.Embed(
            title="**Welcome to Liberty County State!**",
            description="> Thank you for joining LCSRPC, {member.mention}.\n\nLiberty County State Roleplay Community is an ER:LC private server, focused on the community surrounding Liberty County. Departments/Jobs are similar to the ER:LC counterparts, however reflect enhanced realism and roleplay. Liberty County State attempts to host sessions frequently throughout the week, ensuring activity to bring more fun.\n> 1. You must read our server-rules listed in <#1410039042938245163>.\n> 2. You must verify with our automation services in <#1470597322499952791>.\n> 3. In order to learn more about our community, please evaluate our <#1470597313343787030>.\n> 4. If you are ever in need of staff to answer any of your questions, you can create a **General Inquiry** ticket in <#1470597331551387702>.\n\nOtherwise, have a fantastic day, and we hope to see you interact with our community events, channels, and features.".format(member=member)
        )

        embed3 = nextcord.Embed(color=0xffffff)
        embed1.set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484678139601879170/infolo_1.png?ex=69bf19c4&is=69bdc844&hm=d4966d0d1c6f8faca710c8e1dc078ee1b47d9cb12b417450db6d18071f8ce8d3&")

        await channel.send(embeds=[embed1, embed2, embed3])

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
