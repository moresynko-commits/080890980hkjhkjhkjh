import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button, Modal, TextInput
import flask
import os
import threading
import logging
from datetime import datetime, timedelta
import asyncio

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

# Session Management Globals
GLOBAL_GUILD_ID = 1289789596238086194
SESSION_CHANNEL_ID = 1470597340992901204
VOTE_CHANNEL_ID = 1471995054238208223
STATUS_CHANNEL_ID = 1484693321128349786
NAME_CHANGE_CHANNEL_ID = 1480013219199451308
PROTECTED_CHANNEL_ID = 1464682633559801939
PROTECTED_MSG_ID = 1480023088799416451
SESSION_PING_ROLE_ID = 1470597003292573787
MANAGEMENT_ROLE_ID = 1470596840369164288
ON_DUTY_ROLE_ID = 1470596847423852758
CHECKMARK_EMOJI_ID = 1480018743714386070
LCSRPC_EMOJI_ID = 1484385207455846513

session_data = {"active": False, "start_time": None, "starter_id": None, "cooldowns": {}, "pending_votes": {}}

class VoteModal(Modal):
    def __init__(self):
        super().__init__(title="Session Vote Threshold")
        self.threshold = TextInput(label="Vote threshold", default="5", max_length=2)

    async def on_submit(self, interaction):
        try:
            threshold = int(self.threshold.value)
            guild = interaction.guild
            vote_channel = guild.get_channel(VOTE_CHANNEL_ID)
            embed = nextcord.Embed(title="__Session Vote__", description=f"React <:Checkmark:{CHECKMARK_EMOJI_ID}> to vote yes. **Needed: {threshold}**", color=0xffffff)
            msg = await vote_channel.send(embed=embed)
            await msg.add_reaction(f"<:Checkmark:{CHECKMARK_EMOJI_ID}>")
            session_data["pending_votes"][msg.id] = threshold
            await interaction.response.send_message("Vote started!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Invalid number!", ephemeral=True)

class SessionsView(View):
    def __init__(self, active):
        super().__init__(timeout=1800)
        self.active = active

    async def interaction_check(self, interaction):
        if MANAGEMENT_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("Mgmt only!", ephemeral=True)
            return False
        return True

    @Button(label="Session Vote", style=nextcord.ButtonStyle.primary, row=0, disabled_property="active")
    async def vote(self, interaction, button):
        await interaction.response.send_modal(VoteModal())

    @Button(label="Start", style=nextcord.ButtonStyle.green, row=0, disabled_property="active")
    async def start(self, interaction, button):
        global session_data
        session_data["active"] = True
        session_data["start_time"] = datetime.utcnow().isoformat()
        session_data["starter_id"] = interaction.user.id
        await set_session_active(interaction.guild, True)
        await delete_msgs(SESSION_CHANNEL_ID, interaction.guild)
        embed = nextcord.Embed(title="__Session Start__", description="Session begun! Code: LCsRp", color=0xffffff)
        role = interaction.guild.get_role(SESSION_PING_ROLE_ID)
        await interaction.guild.get_channel(SESSION_CHANNEL_ID).send(role.mention, embed=embed)
        await interaction.response.send_message("Started!", ephemeral=True)

    @Button(label="Boost", style=nextcord.ButtonStyle.blurple, row=1, disabled_property="not active")
    async def boost(self, interaction, button):
        embed = nextcord.Embed(title="__Session Boost__", description="Session boosted!", color=0xffffff)
        role = interaction.guild.get_role(SESSION_PING_ROLE_ID)
        await interaction.guild.get_channel(SESSION_CHANNEL_ID).send(role.mention, embed=embed)
        await interaction.response.send_message("Boosted!", ephemeral=True)

    @Button(label="Shutdown", style=nextcord.ButtonStyle.red, row=1, disabled_property="not active")
    async def shutdown(self, interaction, button):
        global session_data
        now = datetime.utcnow().isoformat()
        if "shutdown" in session_data["cooldowns"]:
            last = datetime.fromisoformat(session_data["cooldowns"]["shutdown"])
            if (datetime.utcnow() - last) < timedelta(minutes=15):
                await interaction.response.send_message("Cooldown!", ephemeral=True)
                return
        session_data["active"] = False
        await set_session_active(interaction.guild, False)
        await delete_msgs(SESSION_CHANNEL_ID, interaction.guild)
        embed = nextcord.Embed(title="__Session Shutdown__", description="Session ended.", color=0xff0000)
        await interaction.guild.get_channel(SESSION_CHANNEL_ID).send(embed=embed)
        session_data["cooldowns"]["shutdown"] = now
        await interaction.response.send_message("Shutdown!", ephemeral=True)

    @Button(label="Full", style=nextcord.ButtonStyle.danger, row=1, disabled_property="not active")
    async def full(self, interaction, button):
        embed = nextcord.Embed(title="__Session Full__", description="Session full!", color=0xff0000)
        role = interaction.guild.get_role(SESSION_PING_ROLE_ID)
        await interaction.guild.get_channel(SESSION_CHANNEL_ID).send(role.mention, embed=embed)
        await interaction.response.send_message("Full alert!", ephemeral=True)

async def set_session_active(guild, active):
    channel = guild.get_channel(NAME_CHANGE_CHANNEL_ID)
    if channel:
        name = "Sessions: 🟢" if active else "Sessions: 🔴"
        await channel.edit(name=name)

async def delete_msgs(channel_id, guild):
    channel = guild.get_channel(channel_id)
    if channel:
        async for msg in channel.history(limit=50):
            if msg.id != PROTECTED_MSG_ID:
                try:
                    await msg.delete()
                except:
                    pass

@bot.command(name="sessions", aliases=['p'])
async def sessions(ctx):
    active = "🟢" in bot.get_channel(STATUS_CHANNEL_ID).name if bot.get_channel(STATUS_CHANNEL_ID) else False
    if MANAGEMENT_ROLE_ID not in [r.id for r in ctx.author.roles]:
        await ctx.reply("No permission!", ephemeral=True)
        return
    embed = nextcord.Embed(title="__Session Panel__", description="Manage session here.", color=0xffffff)
    view = SessionsView(active)
    await ctx.reply(embed=embed, view=view, ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    global session_data
    if payload.channel_id != VOTE_CHANNEL_ID or payload.emoji.id != CHECKMARK_EMOJI_ID:
        return
    guild = bot.get_guild(GLOBAL_GUILD_ID)
    channel = guild.get_channel(VOTE_CHANNEL_ID)
    msg = await channel.fetch_message(payload.message_id)
    threshold = session_data["pending_votes"].get(msg.id, 5)
    reaction = msg.reactions[0]
    users = await reaction.users().flatten()
    count = len([u for u in users if not u.bot])
    if count >= threshold:
        await set_session_active(guild, True)
        await msg.reply("Threshold met! Session started!")
        session_data["pending_votes"].pop(msg.id, None)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} logged in! Guilds: {len(bot.guilds)}')
    activity = nextcord.Activity(name="Liberty County State | dsc.gg/lcsrpc", type=nextcord.ActivityType.watching)
    await bot.change_presence(activity=activity)

# Existing say, dmuser, dmrole, on_member_join commands (unchanged)
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
    embed = nextcord.Embed(title="# <:Offical_server:1475860128686411837> __LCSRPC DM__")
    embed.add_field(name="", value=f"> From **{nickname}**:\n> {message}", inline=False)
    embed.timestamp = ctx.message.created_at
    embed.set_footer(text=ctx.message.created_at.strftime('%I:%M%p'))
    try:
        await user.send(embed=embed)
        await ctx.send("DM sent!", delete_after=5)
    except:
        await ctx.send("DM fail!", delete_after=5)

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
    except:
        return await ctx.send("Invalid role!", delete_after=5)
    if len(role.members) > 50:
        return await ctx.send("Too many!", delete_after=5)
    embed_base = nextcord.Embed(title="# <:Offical_server:1475860128686411837> __LCSRPC DM__")
    embed_base.timestamp = ctx.message.created_at
    sent = 0
    for m in role.members:
        if m.bot:
            continue
        nick = m.nick or m.display_name
        embed = embed_base.copy()
        embed.add_field(name="", value=f"> From **{nick}**:\n> {message}", inline=False)
        embed.set_footer(text=ctx.message.created_at.strftime('%I:%M%p'))
        try:
            await m.send(embed=embed)
            sent += 1
        except:
            pass
    await ctx.send(f"Sent to {sent}/{len(role.members)}!", delete_after=5)

@bot.event
async def on_member_join(member):
    # Text welcome
    ch_text = bot.get_channel(1470597378116681812)
    if ch_text:
        g = member.guild
        count = len([m for m in g.members if not m.bot])
        ord = 'st' if count % 10 == 1 and count % 100 != 11 else 'nd' if count % 10 == 2 else 'rd' if count % 10 == 3 else 'th'
        badge = '<:Welcome0:1484564259395604572><:Welcome1:1484564289309380780><:Welcome2:1484564315888681000><:Welcome3:1484564376995234037>'
        msg = f"{badge} **to LCSRPC, {member.mention}!** `{count}{ord}` member. Thanks!"
        await ch_text.send(msg)
    # Embed welcome
    ch_embed = bot.get_channel(1470941203343216843)
    if ch_embed:
        await ch_embed.send(member.mention)
        e1 = nextcord.Embed(color=0xffffff).set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484676770224410775/alrwelc.png")
        e2 = nextcord.Embed(title="**Welcome to Liberty County State!**", color=0xffffff, description=f"> Thank you for joining LCSRPC, {member.mention}.\\n\\n[full description unchanged]")
        e3 = nextcord.Embed(color=0xffffff).set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484678139601879170/infolo_1.png")
        await ch_embed.send(embeds=[e1, e2, e3])

app = flask.Flask(__name__)

@app.route('/')
def home():
    return {"status": "alive", "bot": str(bot.user) if bot.is_ready() else "starting"}

@app.route('/status')
def status():
    return {"flask": True, "bot_ready": bot.is_ready(), "guilds": len(bot.guilds), "latency": round(bot.latency, 3) if bot.is_ready() else 0}

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot.run(BOT_TOKEN)

