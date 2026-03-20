import nextcord
from nextcord.ext import commands
import nextcord.ui
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

# Globals
GLOBAL_GUILD_ID = 1289789596238086194
SESSION_CHANNEL_ID = 1470597340992901204
VOTE_CHANNEL_ID = 1471995054238208223
STATUS_CHANNEL_ID = 1484693321128349786
NAME_CHANGE_CHANNEL_ID = 1480013219199451308
PROTECTED_MSG_ID = 1480023088799416451
SESSION_PING_ROLE_ID = 1470597003292573787
MANAGEMENT_ROLE_ID = 1470596840369164288
CHECKMARK_EMOJI_ID = 1480018743714386070

session_data = {"active": False, "cooldowns": {}, "pending_votes": {}}

class VoteModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="Vote Threshold")
        self.add_item(nextcord.ui.TextInput(label="Number", default="5"))

    async def callback(self, interaction):
        try:
            threshold = int(self.children[0].value)
            guild = interaction.guild
            ch = guild.get_channel(VOTE_CHANNEL_ID)
            embed = nextcord.Embed(title="__Vote__", description=f"React <:Checkmark:{CHECKMARK_EMOJI_ID}> ({threshold} needed)", color=0xffffff)
            msg = await ch.send(embed=embed)
            await msg.add_reaction(f"<:Checkmark:{CHECKMARK_EMOJI_ID}>")
            session_data["pending_votes"][msg.id] = threshold
            await interaction.response.send_message("Vote posted!", ephemeral=True)
        except:
            await interaction.response.send_message("Invalid!", ephemeral=True)

class SessionsView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=1800)

    async def interaction_check(self, interaction):
        if MANAGEMENT_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("No permission!", ephemeral=True)
            return False
        return True

    @nextcord.ui.button(label="Vote", style=nextcord.ButtonStyle.primary)
    async def vote(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        if session_data["active"]:
            await interaction.response.send_message("Active session.", ephemeral=True)
            return
        await interaction.response.send_modal(VoteModal())

    @nextcord.ui.button(label="Start", style=nextcord.ButtonStyle.green)
    async def start(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        if session_data["active"]:
            await interaction.response.send_message("Already active.", ephemeral=True)
            return
        session_data["active"] = True
        await set_session_active(interaction.guild, True)
        await delete_msgs(SESSION_CHANNEL_ID, interaction.guild)
        role = interaction.guild.get_role(SESSION_PING_ROLE_ID)
        ch = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        embed = nextcord.Embed(title="__Session Started__", description="Code: LCsRp", color=0x00ff00)
        await ch.send(role.mention, embed=embed)
        await interaction.response.send_message("Started!", ephemeral=True)

    @nextcord.ui.button(label="Boost", style=nextcord.ButtonStyle.blurple)
    async def boost(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        if not session_data["active"]:
            await interaction.response.send_message("Not active.", ephemeral=True)
            return
        role = interaction.guild.get_role(SESSION_PING_ROLE_ID)
        ch = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        embed = nextcord.Embed(title="__Boost__", description="Join now!", color=0x5865f2)
        await ch.send(role.mention, embed=embed)
        await interaction.response.send_message("Boosted!", ephemeral=True)

    @nextcord.ui.button(label="Shutdown", style=nextcord.ButtonStyle.red)
    async def shutdown(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        if not session_data["active"]:
            await interaction.response.send_message("Not active.", ephemeral=True)
            return
        now = datetime.utcnow().isoformat()
        if "shutdown" in session_data["cooldowns"]:
            if (datetime.utcnow() - datetime.fromisoformat(session_data["cooldowns"]["shutdown"])) < timedelta(minutes=15):
                await interaction.response.send_message("15min cooldown!", ephemeral=True)
                return
        session_data["active"] = False
        await set_session_active(interaction.guild, False)
        await delete_msgs(SESSION_CHANNEL_ID, interaction.guild)
        ch = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        embed = nextcord.Embed(title="__Shutdown__", description="Ended.", color=0xff0000)
        await ch.send(embed=embed)
        session_data["cooldowns"]["shutdown"] = now
        await interaction.response.send_message("Shutdown!", ephemeral=True)

    @nextcord.ui.button(label="Full", style=nextcord.ButtonStyle.danger)
    async def full(self, interaction: nextcord.Interaction, button: nextcord.ui.Button):
        if not session_data["active"]:
            await interaction.response.send_message("Not active.", ephemeral=True)
            return
        role = interaction.guild.get_role(SESSION_PING_ROLE_ID)
        ch = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        embed = nextcord.Embed(title="__Full__", description="Session full!", color=0xff0000)
        await ch.send(role.mention, embed=embed)
        await interaction.response.send_message("Full!", ephemeral=True)

async def set_session_active(guild, active):
    ch = guild.get_channel(NAME_CHANGE_CHANNEL_ID)
    if ch:
        await ch.edit(name="Sessions: 🟢" if active else "Sessions: 🔴")

async def delete_msgs(ch_id, guild):
    ch = guild.get_channel(ch_id)
    if ch:
        async for msg in ch.history(limit=50):
            if msg.id != PROTECTED_MSG_ID:
                try:
                    await msg.delete()
                except:
                    pass

@bot.command(aliases=["p"])
async def sessions(ctx):
    if MANAGEMENT_ROLE_ID not in [r.id for r in ctx.author.roles]:
        await ctx.reply("No!", ephemeral=True)
        return
    embed = nextcord.Embed(title="__Sessions__", description=f"Active: {session_data['active']}", color=0xffffff)
    view = SessionsView()
    await ctx.reply(embed=embed, view=view, ephemeral=True)

@bot.event
async def on_raw_reaction_add(self, payload):
    if payload.channel_id != VOTE_CHANNEL_ID or payload.emoji.id != CHECKMARK_EMOJI_ID:
        return
    guild = bot.get_guild(GLOBAL_GUILD_ID)
    ch = guild.get_channel(VOTE_CHANNEL_ID)
    msg = await ch.fetch_message(payload.message_id)
    threshold = session_data["pending_votes"].get(msg.id, 5)
    rxn = msg.reactions[0]
    users = await rxn.users().flatten()
    count = sum(1 for u in users if not u.bot)
    if count >= threshold:
        session_data["active"] = True
        await set_session_active(guild, True)
        await msg.reply("Started by votes!")
        session_data["pending_votes"].pop(msg.id, None)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} logged in!')
    await bot.change_presence(activity=nextcord.Activity(name="Liberty County State | dsc.gg/lcsrpc", type=nextcord.ActivityType.watching))

@bot.command()
async def say(ctx, *, message):
    if not any(r.id in [1470596832794251408, 1470596825575854223, 1470596818298601567] for r in ctx.author.roles):
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
async def dmuser(ctx, userid: str, *, message):
    if not any(r.id in [1470596825575854223, 1470596832794251408, 1470596818298601567] for r in ctx.author.roles):
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    g = bot.get_guild(1289789596238086194)
    user = await commands.MemberConverter().convert(ctx, userid) if userid.startswith('<') else await bot.fetch_user(int(userid))
    nick = (g.get_member(user.id) or user).nick or user.display_name
    e = nextcord.Embed(title="LCSRPC DM", description=f"> From **{nick}**: {message}", timestamp=ctx.message.created_at)
    e.set_footer(text=e.timestamp.strftime('%I:%M%p'))
    try:
        await user.send(embed=e)
        await ctx.send("Sent!", delete_after=5)
    except:
        await ctx.send("Failed!", delete_after=5)

@bot.command()
async def dmrole(ctx, roleid: str, *, message):
    if 1470596818298601567 not in [r.id for r in ctx.author.roles]:
        await ctx.send("No!", delete_after=5)
        return
    await ctx.message.delete()
    g = bot.get_guild(1289789596238086194)
    role_id = int(''.join(c for c in roleid if c.isdigit()))
    role = g.get_role(role_id)
    if not role or len([m for m in role.members if not m.bot]) > 50:
        await ctx.send("Invalid or too big!", delete_after=5)
        return
    sent = 0
    for m in role.members:
        if m.bot:
            continue
        nick = m.nick or m.display_name
        e = nextcord.Embed(title="LCSRPC DM", description=f"> From **{nick}**: {message}", timestamp=ctx.message.created_at)
        e.set_footer(text=e.timestamp.strftime('%I:%M%p'))
        try:
            await m.send(embed=e)
            sent += 1
        except:
            pass
    await ctx.send(f"Sent to {sent}", delete_after=5)

@bot.event
async def on_member_join(member):
    # Text welcome
    ch = bot.get_channel(1470597378116681812)
    if ch:
        count = len([m for m in member.guild.members if not m.bot])
        ordinal = lambda n: "st" if n%10==1 and n%100!=11 else "nd" if n%10==2 else "rd" if n%10==3 else "th"
        msg = f"<:Welcome0:1484564259395604572><:Welcome1:1484564289309380780><:Welcome2:1484564315888681000><:Welcome3:1484564376995234037> **to LCSRPC {member.mention}!** {count}{ordinal(count)} member!"
        await ch.send(msg)
    # Embed welcome
    ch = bot.get_channel(1470941203343216843)
    if ch:
        await ch.send(member.mention)
        e1 = nextcord.Embed(color=0xffffff).set_image(url="https://cdn.discordapp.com/attachments/1484676715010588793/1484676770224410775/alrwelc.png")
        e2 = nextcord.Embed(title="Welcome to Liberty County State!", description="> Thank you {member.mention}. Liberty County State is ER:LC RP server. Read rules <#1410039042938245163>, verify <#1470597322499952791>, info <#1470597313343787030>, ticket <#1470597331551387702>.".format(member=member), color=0xffffff)
        await ch.send(embeds=[e1, e2])

app = flask.Flask(__name__)

@app.route('/')
def home():
    return {"status": "alive"}

@app.route('/status')
def status():
    return {"bot": bot.is_ready(), "guilds": len(bot.guilds)}

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)), debug=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot.run(BOT_TOKEN)

