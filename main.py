import nextcord
from nextcord.ext import commands
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

# Constants
GUILD_ID = 1289789596238086194
SESSION_CHANNEL_ID = 1470597340992901204
VOTE_CHANNEL_ID = 1471995054238208223
NAME_CHANGE_CHANNEL_ID = 1480013219199451308
PROTECTED_MSG_ID = 1480023088799416451
SESSION_PING_ROLE = 1470597003292573787
MANAGEMENT_ROLE = 1470596840369164288
CHECKMARK = 1480018743714386070
LEADERSHIP = 1470596818298601567
EXEC = 1470596825575854223
ADMIN_ROLES = [EXEC, 1470596832794251408, LEADERSHIP]

session_data = {"active": False, "cooldowns": {}, "pending_votes": {}}

class VoteModal(nextcord.ui.Modal, title="Vote Threshold"):
    threshold = nextcord.ui.TextInput(label="Votes needed", default="5")

    async def on_submit(self, interaction):
        try:
            t = int(self.threshold.value)
            c = interaction.guild.get_channel(VOTE_CHANNEL_ID)
            e = nextcord.Embed(title="Vote", description=f"React <:Checkmark:{CHECKMARK}> ({t} needed)", color=0xffffff)
            m = await c.send(embed=e)
            await m.add_reaction(f"<:Checkmark:{CHECKMARK}>")
            session_data["pending_votes"][m.id] = t
            await interaction.response.send_message("Started!", ephemeral=True)
        except:
            await interaction.response.send_message("Invalid!", ephemeral=True)

class SessionsView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=1800)

    async def interaction_check(self, interaction):
        mgmt_roles = [1470596840369164288, 1470596832794251408, 1470596825575854223, 1470596818298601567]
        if MANAGEMENT_ROLE not in [r.id for r in interaction.user.roles] and all(r.id not in mgmt_roles for r in interaction.user.roles):
            await interaction.response.send_message("Management and above only!", ephemeral=True)
            return False
        return True

    @nextcord.ui.button(label="Vote", style=nextcord.ButtonStyle.primary)
    async def vote(self, interaction, b):
        await interaction.response.send_modal(VoteModal())

    @nextcord.ui.button(label="Start", style=nextcord.ButtonStyle.green)
    async def start(self, interaction, b):
        if session_data["active"]:
            return await interaction.response.send_message("Already!", ephemeral=True)
        session_data["active"] = True
        await set_active(interaction.guild, True)
        await clear_session(interaction.guild)
        r = interaction.guild.get_role(SESSION_PING_ROLE)
        c = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        e = nextcord.Embed(title="Session Started", description="LCsRp", color=0x00ff00)
        await c.send(r.mention, embed=e)
        await interaction.response.send_message("Started!", ephemeral=True)

    @nextcord.ui.button(label="Boost", style=nextcord.ButtonStyle.blurple)
    async def boost(self, interaction, b):
        if not session_data["active"]:
            return await interaction.response.send_message("Inactive!", ephemeral=True)
        r = interaction.guild.get_role(SESSION_PING_ROLE)
        c = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        e = nextcord.Embed(title="Boost", description="Join!", color=0x5865f2)
        await c.send(r.mention, embed=e)
        await interaction.response.send_message("Boosted!", ephemeral=True)

    @nextcord.ui.button(label="Shutdown", style=nextcord.ButtonStyle.red)
    async def shutdown(self, interaction, b):
        if not session_data["active"]:
            return await interaction.response.send_message("Inactive!", ephemeral=True)
        now = datetime.now().isoformat()
        if "shutdown" in session_data["cooldowns"] and (datetime.now() - datetime.fromisoformat(session_data["cooldowns"]["shutdown"])) < timedelta(minutes=15):
            return await interaction.response.send_message("Cooldown!", ephemeral=True)
        session_data["active"] = False
        await set_active(interaction.guild, False)
        await clear_session(interaction.guild)
        c = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        e = nextcord.Embed(title="Shutdown", description="Ended", color=0xff0000)
        await c.send(embed=e)
        session_data["cooldowns"]["shutdown"] = now
        await interaction.response.send_message("Shutdown!", ephemeral=True)

    @nextcord.ui.button(label="Full", style=nextcord.ButtonStyle.danger)
    async def full(self, interaction, b):
        if not session_data["active"]:
            return await interaction.response.send_message("Inactive!", ephemeral=True)
        r = interaction.guild.get_role(SESSION_PING_ROLE)
        c = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        e = nextcord.Embed(title="Full", description="Full!", color=0xff0000)
        await c.send(r.mention, embed=e)
        await interaction.response.send_message("Full!", ephemeral=True)

async def set_active(guild, active):
    c = guild.get_channel(NAME_CHANGE_CHANNEL_ID)
    if c:
        await c.edit(name="🟢 Sessions" if active else "🔴 Sessions")

async def clear_session(guild):
    c = guild.get_channel(SESSION_CHANNEL_ID)
    if c:
        async for m in c.history(limit=50):
            if m.id != PROTECTED_MSG_ID:
                try:
                    await m.delete()
                except:
                    pass

@bot.command(aliases=["p"])
async def sessions(ctx):
    mgmt_roles = [1470596840369164288, 1470596832794251408, 1470596825575854223, 1470596818298601567]
    if MANAGEMENT_ROLE not in [r.id for r in ctx.author.roles] and all(r.id not in mgmt_roles for r in ctx.author.roles):
        await ctx.send("Management and above only!", delete_after=5)
        return
    e = nextcord.Embed(title="Sessions Panel", color=0xffffff)
    v = SessionsView()
    await ctx.reply(embed=e, view=v, ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != VOTE_CHANNEL_ID or payload.emoji.id != CHECKMARK:
        return
    g = bot.get_guild(GUILD_ID)
    c = g.get_channel(VOTE_CHANNEL_ID)
    m = await c.fetch_message(payload.message_id)
    t = session_data["pending_votes"].get(m.id, 5)
    rx = m.reactions[0]
    u = await rx.users().flatten()
    cnt = sum(1 for user in u if not user.bot)
    if cnt >= t:
        session_data["active"] = True
        await set_active(g, True)
        await m.reply("Session started by vote!")
        session_data["pending_votes"].pop(m.id)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} ready!')
    await bot.change_presence(activity=nextcord.Activity(name="Liberty County | dsc.gg/lcsrpc", type=nextcord.ActivityType.watching))

@bot.command()
async def say(ctx, *, msg):
    if not any(r.id in ADMIN_ROLES for r in ctx.author.roles):
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    await ctx.send(msg)

@bot.command()
async def dmuser(ctx, uid: str, *, msg):
    if not any(r.id in ADMIN_ROLES for r in ctx.author.roles):
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    g = bot.get_guild(GUILD_ID)
    try:
        user = g.get_member(int(uid.lstrip('<@!'))) or await bot.fetch_user(int(uid.lstrip('<@!')))
    except:
        await ctx.send("Invalid user!", delete_after=5)
        return
    e = nextcord.Embed(title="LCSRPC DM", description=f"> **{user.display_name}**:\n> {msg}", timestamp=ctx.message.created_at)
    e.set_footer(text=e.timestamp.strftime('%I:%M%p'))
    try:
        await user.send(embed=e)
        await ctx.send("Sent!", delete_after=5)
    except:
        await ctx.send("Failed!", delete_after=5)

@bot.command()
async def dmrole(ctx, rid: str, *, msg):
    if LEADERSHIP not in [r.id for r in ctx.author.roles]:
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    g = bot.get_guild(GUILD_ID)
    role_id = int(''.join(d for d in rid if d.isdigit()))
    r = g.get_role(role_id)
    if not r or len([m for m in r.members if not m.bot]) > 50:
        await ctx.send("Too big/invalid!", delete_after=5)
        return
    count = 0
    for m in r.members:
        if m.bot:
            continue
        e = nextcord.Embed(title="LCSRPC DM", description=f"> **{m.display_name}**:\n> {msg}", timestamp=ctx.message.created_at)
        e.set_footer(text=e.timestamp.strftime('%I:%M%p'))
        try:
            await m.send(embed=e)
            count += 1
        except:
            pass
    await ctx.send(f"Sent to {count}", delete_after=5)

@bot.event
async def on_member_join(member):
    # Text channel
    ch = bot.get_channel(1470597378116681812)
    if ch:
        count = len([m for m in member.guild.members if not m.bot])
        o = "st" if count % 10 == 1 and count % 100 != 11 else "nd" if count % 10 == 2 else "rd" if count % 10 == 3 else "th"
        await ch.send(f"<:Welcome0:1484564259395604572><:Welcome1:1484564289309380780><:Welcome2:1484564315888681000><:Welcome3:1484564376995234037> **{member.mention}**! #{count}{o} member!")
    # Embed channel
    ch = bot.get_channel(1470941203343216843)
    if ch:
        await ch.send(member.mention)
        e1 = nextcord.Embed(color=0xffffff).set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484676770224410775/alrwelc.png?ex=69bf187d&is=69bdc6fd&hm=93aa43677dac68a2b37ac68dc12d7f151c4d45cdf9a7f976df3e9e88b17022d1&")
        e2 = nextcord.Embed(title="Welcome to Liberty County State!", description=f"**Thank you for joining LCSRPC, {member.mention}.**\n\nLiberty County State Roleplay Community (ER:LC private server).\nRules: <#1410039042938245163>\nVerify: <#1470597322499952791>\nInfo: <#1470597313343787030>\nTicket: <#1470597331551387702>\n\nHave a great day!", color=0xffffff)
        await ch.send(embeds=[e1, e2])

app = flask.Flask(__name__)

@app.route('/')
@app.route('/status')
def status():
    return {"status": "alive", "bot": bot.is_ready()}

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)), debug=False)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    bot.run(BOT_TOKEN)
