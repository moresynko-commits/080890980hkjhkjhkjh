import nextcord
from nextcord.ext import commands
import flask
import os
import threading
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
    allowed_roles = [1470596832794251408, 1470596825575854223, 1470596818298601567]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.send("No permission!", delete_after=5)
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
async def dmuser(ctx, userid: str, *, message: str):
    exec_roles = [1470596825575854223, 1470596832794251408, 1470596818298601567]
    if not any(role.id in exec_roles for role in ctx.author.roles):
        return await ctx.send("No permission!", delete_after=5)
    await ctx.message.delete()

    guild = bot.get_guild(1289789596238086194)
    if not guild:
        return await ctx.send("Guild not found!", delete_after=5)

    try:
        user_id = int(''.join(filter(str.isdigit, userid)))
        user = await bot.fetch_user(user_id)
    except:
        try:
            user = await commands.MemberConverter().convert(ctx, userid)
        except:
            return await ctx.send("Invalid user!", delete_after=5)

    member = guild.get_member(user.id)
    nickname = member.nick if member and member.nick else user.display_name

    embed = nextcord.Embed(title="# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__")
    embed.add_field(name="", value=f"> From **{nickname}**:\n> {message}", inline=False)
    embed.timestamp = ctx.message.created_at
    embed.set_footer(text=ctx.message.created_at.strftime('%I:%M%p'))

    try:
        await user.send(embed=embed)
        await ctx.send("DM sent!", delete_after=5)
    except:
        await ctx.send("Failed to send DM!", delete_after=5)

@bot.command()
async def dmrole(ctx, roleid: str, *, message: str):
    if 1470596818298601567 not in [role.id for role in ctx.author.roles]:
        return await ctx.send("No permission!", delete_after=5)
    await ctx.message.delete()

    guild = bot.get_guild(1289789596238086194)
    if not guild:
        return await ctx.send("Guild not found!", delete_after=5)

    try:
        role_id = int(''.join(filter(str.isdigit, roleid)))
        role = guild.get_role(role_id)
        if not role:
            return await ctx.send("Role not found!", delete_after=5)
    except:
        return await ctx.send("Invalid role!", delete_after=5)

    if len(role.members) > 50:
        return await ctx.send("Too many members!", delete_after=5)

    embed_base = nextcord.Embed(title="# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__")
    embed_base.timestamp = ctx.message.created_at
    sent = 0
    for member in role.members:
        if member.bot:
            continue
        nick = member.nick or member.display_name
        embed = embed_base.copy()
        embed.add_field(name="", value=f"> From **{nick}**:\n> {message}", inline=False)
        embed.set_footer(text=ctx.message.created_at.strftime('%I:%M%p'))
        try:
            await member.send(embed=embed)
            sent += 1
        except:
            pass
    await ctx.send(f"DM sent to {sent}/{len(role.members)}!", delete_after=5)

@bot.event
async def on_member_join(member):
    # Text welcome to 1470597378116681812
    channel_text = bot.get_channel(1470597378116681812)
    if channel_text:
        guild = member.guild
        human_count = len([m for m in guild.members if not m.bot])
        ordinal = 'st' if human_count % 10 == 1 and human_count % 100 != 11 else 'nd' if human_count % 10 == 2 and human_count % 100 != 12 else 'rd' if human_count % 10 == 3 and human_count % 100 != 13 else 'th'
        emoji_badge = '<:Welcome0:1484564259395604572><:Welcome1:1484564289309380780><:Welcome2:1484564315888681000><:Welcome3:1484564376995234037>'
        msg = f"{emoji_badge} **to Liberty County State Roleplay Community, {member.mention}.** You are our `{human_count}{ordinal}` member.\n> Thanks for participating in our community by joining and we hope to see you soon!"
        await channel_text.send(msg)

    # Embed welcome to 1470941203343216843
    channel_embed = bot.get_channel(1470941203343216843)
    if channel_embed:
        await channel_embed.send(member.mention)

        embed1 = nextcord.Embed(color=0xffffff)
        embed1.set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484676770224410775/alrwelc.png?ex=69bf187d&is=69bdc6fd&hm=93aa43677dac68a2b37ac68dc12d7f151c4d45cdf9a7f976df3e9e88b17022d1&")

        embed2 = nextcord.Embed(
            color=0xffffff,
            title="Welcome to Liberty County State!",
            description="> Thank you for joining LCSRPC, {member.mention}.\\n\\nLiberty County State Roleplay Community is an ER:LC private server, focused on the community surrounding Liberty County. Departments/Jobs are similar to the ER:LC counterparts, however reflect enhanced realism and roleplay. Liberty County State attempts to host sessions frequently throughout the week, ensuring activity to bring more fun.\\n\\n> 1. You must read our server-rules listed in <#1410039042938245163>.\\n> 2. You must verify with our automation services in <#1470597322499952791>.\\n> 3. In order to learn more about our community, please evaluate our <#1470597313343787030>.\\n> 4. If you are ever in need of staff to answer any of your questions, you can create a **General Inquiry** ticket in <#1470597331551387702>.\\n\\nOtherwise, have a fantastic day, and we hope to see you interact with our community events, channels, and features.".format(member=member)
        )

        embed3 = nextcord.Embed(color=0xffffff)
        embed3.set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484678139601879170/infolo_1.png?ex=69bf19c4&is=69bdc844&hm=d4966d0d1c6f8faca710c8e1dc078ee1b47d9cb12b417450db6d18071f8ce8d3&")

        await channel_embed.send(embeds=[embed1, embed2, embed3])

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
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot.run(BOT_TOKEN)
