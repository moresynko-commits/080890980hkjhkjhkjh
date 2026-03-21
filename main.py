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

# Guild & Channel IDs
GUILD_ID = 1289789596238086194
SESSION_CHANNEL_ID = 1470597340992901204
VOTE_CHANNEL_ID = 1471995054238208223
NAME_CHANGE_CHANNEL_ID = 1480013219199451308
PROTECTED_MSG_ID = 1480023088799416451

# Roles
SESSION_PING_ROLE = 1470597003292573787
CHECKMARK = 1480018743714386070
MANAGEMENT_ROLE = 1470596840369164288
DIRECTORS_ROLE = 1470596832794251408
EXEC_ROLE = 1470596825575854223
LEADERSHIP_ROLE = 1470596818298601567
SUPERVISORY_ROLE = 1470596865601966203
INTERNAL_AFFAIRS_ROLE = 1470596874552606942
ADMIN_ROLE = 1470596884547764419
MODERATION_ROLE = 1470596891782938665
STAFF_TRAINER_ROLE = 1470596876662345790
STAFF_ACADEMY_ROLE = 1470596894907695188
STAFF_MEMBER_ROLE = 1470596943393849364
ADMIN_ROLES = [EXEC_ROLE, DIRECTORS_ROLE, LEADERSHIP_ROLE]
MGMT_ROLES = [MANAGEMENT_ROLE, DIRECTORS_ROLE, EXEC_ROLE, LEADERSHIP_ROLE]

session_data = {"active": False, "cooldowns": {}, "pending_votes": {}}

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

class VoteModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="Vote Threshold")
        self.threshold = nextcord.ui.TextInput(label="Votes needed", placeholder="5")
        self.add_item(self.threshold)

    async def on_submit(self, interaction):
        try:
            t = int(self.threshold.value)
            c = interaction.guild.get_channel(VOTE_CHANNEL_ID)
            e = nextcord.Embed(title="Vote", description=f"React <:Checkmark:{CHECKMARK}> ({t} needed)", color=0xffffff)
            m = await c.send(embed=e)
            await m.add_reaction(f"<:Checkmark:{CHECKMARK}>")
            session_data["pending_votes"][m.id] = t
            await interaction.response.send_message("Vote posted!", ephemeral=True)
        except:
            await interaction.response.send_message("Invalid number!", ephemeral=True)

class SessionsView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=1800)

    async def interaction_check(self, interaction):
        if all(r.id not in MGMT_ROLES for r in interaction.user.roles):
            await interaction.response.send_message("Mgmt+, Directors, Exec, Leadership only!", ephemeral=True)
            return False
        return True

    @nextcord.ui.button(label="Vote", style=nextcord.ButtonStyle.primary)
    async def vote(self, interaction, button):
        await interaction.response.send_modal(VoteModal())

    @nextcord.ui.button(label="Start", style=nextcord.ButtonStyle.green)
    async def start(self, interaction, button):
        if session_data["active"]:
            return await interaction.response.send_message("Already active!", ephemeral=True)
        session_data["active"] = True
        await set_active(interaction.guild, True)
        await clear_session(interaction.guild)
        r = interaction.guild.get_role(SESSION_PING_ROLE)
        c = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        e = nextcord.Embed(title="Session Started", description="LCsRp", color=0x00ff00)
        await c.send(r.mention, embed=e)
        await interaction.response.send_message("Started!", ephemeral=True)

    @nextcord.ui.button(label="Boost", style=nextcord.ButtonStyle.blurple)
    async def boost(self, interaction, button):
        if not session_data["active"]:
            return await interaction.response.send_message("Inactive!", ephemeral=True)
        r = interaction.guild.get_role(SESSION_PING_ROLE)
        c = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        e = nextcord.Embed(title="Boost", description="Join!", color=0x5865f2)
        await c.send(r.mention, embed=e)
        await interaction.response.send_message("Boosted!", ephemeral=True)

    @nextcord.ui.button(label="Shutdown", style=nextcord.ButtonStyle.red)
    async def shutdown(self, interaction, button):
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
    async def full(self, interaction, button):
        if not session_data["active"]:
            return await interaction.response.send_message("Inactive!", ephemeral=True)
        r = interaction.guild.get_role(SESSION_PING_ROLE)
        c = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        e = nextcord.Embed(title="Full", description="Full!", color=0xff0000)
        await c.send(r.mention, embed=e)
        await interaction.response.send_message("Full!", ephemeral=True)

@bot.command()
async def sessions(ctx):
    if ctx.guild.id != GUILD_ID:
        return
    if all(r.id not in MGMT_ROLES for r in ctx.author.roles):
        await ctx.send("Mgmt+, Directors, Exec, Leadership only!", delete_after=5)
        return
    embed = nextcord.Embed(title="Sessions Panel", description=f"Active: {session_data['active']}", color=0xffffff)
    view = SessionsView()
    await ctx.reply(embed=embed, view=view, ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != VOTE_CHANNEL_ID or payload.emoji.id != CHECKMARK:
        return
    g = bot.get_guild(GUILD_ID)
    if not g:
        return
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
    if ctx.guild.id != GUILD_ID:
        return
    if not any(r.id in ADMIN_ROLES for r in ctx.author.roles):
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    await ctx.send(msg)

@bot.command()
async def dmuser(ctx, uid: str, *, msg):
    if ctx.guild.id != GUILD_ID:
        return
    if not any(r.id in ADMIN_ROLES for r in ctx.author.roles):
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    g = bot.get_guild(GUILD_ID)
    try:
        user_id = int(uid.lstrip('<@!'))
        user = g.get_member(user_id) or await bot.fetch_user(user_id)
    except:
        await ctx.send("Invalid user!", delete_after=5)
        return
    e = nextcord.Embed(title="# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__", description=f"> From **{ctx.author.display_name}**:\n> {msg}\n-# Sent at {ctx.message.created_at.strftime('%I:%M%p')}", color=0x2b2d31)
    try:
        await user.send(embed=e)
        await ctx.send("DM sent!", delete_after=5)
    except:
        await ctx.send("Failed to DM!", delete_after=5)

@bot.command()
async def dmrole(ctx, rid: str, *, msg):
    if ctx.guild.id != GUILD_ID:
        return
    if LEADERSHIP_ROLE not in [r.id for r in ctx.author.roles]:
        await ctx.send("Leadership only!", delete_after=5)
        return
    await ctx.message.delete()
    g = bot.get_guild(GUILD_ID)
    role_id = int(''.join(d for d in rid if d.isdigit()))
    r = g.get_role(role_id)
    if not r or len([m for m in r.members if not m.bot]) > 50:
        await ctx.send("Too big/invalid role!", delete_after=5)
        return
    count = 0
    for m in r.members:
        if m.bot:
            continue
        e = nextcord.Embed(title="# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__", description=f"> From **{ctx.author.display_name}**:\n> {msg}\n-# Sent at {ctx.message.created_at.strftime('%I:%M%p')}", color=0x2b2d31)
        try:
            await m.send(embed=e)
            count += 1
        except:
            pass
    await ctx.send(f"DM sent to {count}/{len(r.members)}", delete_after=5)

@bot.event
async def on_member_join(member):
    guild = member.guild
    if guild.id != GUILD_ID:
        return
    # Text channel old format
    ch = bot.get_channel(1470597378116681812)
    if ch:
        human_count = len([m for m in guild.members if not m.bot])
        ordinal = 'st' if human_count % 10 == 1 and human_count % 100 != 11 else 'nd' if human_count % 10 == 2 and human_count % 100 != 12 else 'rd' if human_count % 10 == 3 and human_count % 100 != 13 else 'th'
        emoji_badge = '<:Welcome0:1484564259395604572><:Welcome1:1484564289309380780><:Welcome2:1484564315888681000><:Welcome3:1484564376995234037>'
        msg = f"{emoji_badge} ** to Liberty County State Roleplay Community (LCSRPC), {member.mention}.** You are our `{human_count}{ordinal}` member. > Thanks for joining, and have a wonderful day!"
        await ch.send(msg)
    # Embed channel exact
    ch = bot.get_channel(1470941203343216843)
    if ch:
        await ch.send(member.mention)
        embed1 = nextcord.Embed(color=0xffffff)
        embed1.set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484676770224410775/alrwelc.png?ex=69bf187d&is=69bdc6fd&hm=93aa43677dac68a2b37ac68dc12d7f151c4d45cdf9a7f976df3e9e88b17022d1&")
        embed2 = nextcord.Embed(
            title="**Welcome to Liberty County State!**",
            description="> Thank you for joining LCSRPC, {member.mention}.\\n\\nLiberty County State Roleplay Community is an ER:LC private server, focused on the community surrounding Liberty County. Departments/Jobs are similar to the ER:LC counterparts, however reflect enhanced realism and roleplay. Liberty County State attempts to host sessions frequently throughout the week, ensuring activity to bring more fun.\\n> 1. You must read our server-rules listed in <#1410039042938245163>.\\n> 2. You must verify with our automation services in <#1470597322499952791>.\\n> 3. In order to learn more about our community, please evaluate our <#1470597313343787030>.\\n> 4. If you are ever in need of staff to answer any of your questions, you can create a **General Inquiry** ticket in <#1470597331551387702>.\\n\\nOtherwise, have a fantastic day, and we hope to see you interact with our community events, channels, and features.".format(member=member)
        )
        await ch.send(embeds=[embed1, embed2])

app = flask.Flask(__name__)

@app.route('/')
@app.route('/status')
def status():
    return {"status": "alive", "bot": bot.is_ready()}

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)), debug=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    asyncio.run(bot.start(BOT_TOKEN))
