const { Client, GatewayIntentBits, EmbedBuilder, ActionRowBuilder, StringSelectMenuBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle, ChannelType } = require('discord.js');
const express = require('express');
const path = require('path');

const client = new Client({ 
intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMessageReactions
  ]
});

const token = process.env.BOT_TOKEN;
const GUILD_ID = '1289789596238086194';
const SESSION_CHANNEL = '1470597340992901204';
const VOTE_CHANNEL = '1471995054238208223';
const NAME_CHANNEL = '1480013219199451308';
const PROTECTED_MSG = '1484784024491790469';

const WELCOME_TEXT = '1470597378116681812';
const WELCOME_EMBED = '1470941203343216843';
const PING_ROLE = '1470597003292573787';

const CHECKMARK_EMOJI = '1480018743714386070';

const GENERAL_CHANNEL = '1470597378116681812';
const SESSION_PARENT_CHANNEL = '1484693321128349786';
const SESSION_PARENT_CAT = '1470597251154972794';

const LCSRPC_EMOJI = '<:LCSRPC:1484385207455846513>';
const HEAD_IMG = 'https://cdn.discordapp.com/attachments/1484676715010588793/1484693166270714007/lcsrpcsess.png?ex=69bf27c3&is=69bdd643&hm=07aba51b706c19670195fd44dc3f4a09f87a49f2abb8b2096cc97ee19158d06d&';
const FOOTER_IMG = 'https://cdn.discordapp.com/attachments/1484676715010588793/1484678139601879170/infolo_1.png?ex=69bf19c4&is=69bdc844&hm=d4966d0d1c6f8faca710c8e1dc078ee1b47d9cb12b417450db6d18071f8ce8d3&';
const ECON_HEADER_IMG = 'https://cdn.discordapp.com/attachments/1484676715010588793/1484755986320330954/econlcs.png?ex=69bf6244&is=69be10c4&hm=cd7f65661d99188815c42560eb732f6969966389ae34b9546cdedc10757a2d65&';

const MGMT_ROLES = ['1470596840369164288', '1470596832794251408', '1470596825575854223', '1470596818298601567'];

const ADMIN_ROLES = ['1470596825575854223', '1470596832794251408', '1470596818298601567'];
const LEADERSHIP_ROLE = '1470596818298601567';

const CHAIRMAN_ROLE = '1470596810945859742';
const LEADERSHIP_IMMUNE = ['1470596818298601567']; // Immune rob/cd
const COMMUNITY_ROLE = '1470596942198472977';
const CASH_LORD_ROLE = '1470597009001156620'; // 7.5m
const MONEY_MAKER_ROLE = '1470597009948934239'; // 5m
const BANK_WORKER_ROLE = '1470597011047710894'; // 2.5m
const BOD_EXEC_LEAD_ROLES = ADMIN_ROLES;

const BOT_CHANNELS = ['1470597383480934562', '1484402222640009357', '1470597465681035388'];
const ECON_LOGS_CHANNEL = '1484755057240047616';
const TRAINING_REQ_CHANNEL = '1484757004386832434';
const TRAINER_ROLE = '1470596876662345790';
const TRAINEE_ROLE = '1470596894907695188';

let sessionData = { active: false, cooldowns: {}, pendingVotes: {}, starterId: null, startTime: null, checkTimers: [], voteMsgIds: [] };
let afkUsers = {}; // {userId: {reason, oldNick, pings: []}}

const AFK_PREFIX = 'AFK | ';

const app = express();
app.use(express.json());
app.get('/', (req, res) => res.json({ status: 'alive' }));
app.get('/status', (req, res) => res.json({ status: 'alive', bot: client.isReady() ? 'ready' : 'starting' }));

const port = process.env.PORT || 5000;
app.listen(port, '0.0.0.0', () => console.log(`Server on port ${port}`));

client.once('ready', async () => {
  console.log(`${client.user.tag} ready!`);
  client.user.setPresence({ activities: [{ name: 'Liberty County | dsc.gg/lcsrpc', type: 3 }] });
  const guild = client.guilds.cache.get(GUILD_ID);
  if (guild) {
    await guild.commands.set([
      {
        name: 'sessions',
        description: 'Sessions panel'
      },
      {
        name: 'say',
        description: 'Say something',
        options: [{
          type: 3,
          name: 'msg',
          description: 'Message',
          required: true
        }]
      },
      {
        name: 'dmuser',
        description: 'DM user',
        options: [{
          type: 3,
          name: 'uid',
          description: 'User ID/mention',
          required: true
        }, {
          type: 3,
          name: 'msg',
          description: 'Message',
          required: true
        }]
      },
      {
        name: 'dmrole',
        description: 'DM role members',
        options: [{
          type: 3,
          name: 'rid',
          description: 'Role ID/mention',
          required: true
        }, {
          type: 3,
          name: 'msg',
          description: 'Message',
          required: true
        }]
      },
      {
        name: 'balance',
        description: 'Check balance',
      },
      {
        name: 'bal',
        description: 'Check balance (alias)',
      },
      {
        name: 'work',
        description: 'Work for money (1h cd)'
      },
      {
        name: 'daily',
        description: 'Daily reward (24h cd)'
      },
      {
        name: 'leaderboard',
        description: 'Top balances',
        name_localizations: { 'en-US': 'leaderboard', 'en-GB': 'lb' }
      },
      {
        name: 'lb',
        description: 'Top balances (alias)'
      },
      {
        name: 'requesttraining',
        description: 'Request staff training',
      },
      {
        name: 'afk',
        description: 'Set AFK',
        options: [{
          type: 3,
          name: 'reason',
          description: 'Reason (optional)',
          required: false
        }]
      }
    ]);

    console.log('Slash commands registered!');
  }
});

client.on('interactionCreate', async interaction => {
  if (!interaction.isChatInputCommand() && !interaction.isStringSelectMenu() && !interaction.isButton() && !interaction.isModalSubmit()) return;
  
  if (interaction.isStringSelectMenu()) {
    if (interaction.customId === 'starter_check' || interaction.customId === 'mgmt_check') {
      await interaction.deferUpdate();
      const value = interaction.values[0];
      const guild = interaction.guild || client.guilds.cache.get(GUILD_ID);
      if (value === 'check_no') {
        await shutdownSession(guild);
        interaction.followUp({ content: 'Session shutdown via DM check.', ephemeral: true });
      } else {
        const timer = setTimeout(() => dmSessionCheck(guild, sessionData.starterId || 'unknown', false), 3600000);
        sessionData.checkTimers.push(timer);
        interaction.followUp({ content: 'Check rescheduled (1h).', ephemeral: true });
      }
      return;
    }
    
    if (interaction.customId === 'session_menu') {
      const guild = interaction.guild;
      const value = interaction.values[0];
      await interaction.deferUpdate();
      const member = interaction.member;
      if (!MGMT_ROLES.some(id => member.roles.cache.has(id))) {
        return interaction.followUp({ content: 'Mgmt+ only!', ephemeral: true });
      }
      
      const isActive = await getSessionActive(guild);
      
      switch (value) {
        case 'session_vote':
          const modal = new ModalBuilder()
            .setCustomId('vote_modal')
            .setTitle('Session Vote');
          const input = new TextInputBuilder()
            .setCustomId('threshold')
            .setLabel('How many votes do you wish the session vote receive before you are notified to begin a new session?')
            .setStyle(TextInputStyle.Short)
            .setPlaceholder('5')
            .setMinLength(1)
            .setMaxLength(2);
          modal.addComponents(new ActionRowBuilder().addComponents(input));
          await interaction.showModal(modal);
          break;
        
        case 'session_start':
          if (isActive) return interaction.followUp({ content: 'Session already active!', ephemeral: true });
          await clearSession(guild, false);
          await set_active(guild, true);
          const staffCount = await getStaffCount(guild);
          const embed1s = new EmbedBuilder().setImage(HEAD_IMG).setColor(0xffffff);
          const embed2s = new EmbedBuilder()
            .setTitle(`${LCSRPC_EMOJI} | LCSRPC Session Started`)
            .setDescription(`After votes received, a session has begun in Liberty County State Roleplay Community. Please refer below for more information.\\n- **In-Game Code:** \`LCsRp\`\\n- **Players:** 5/40\\n- **Staff Online:** ${staffCount}`)
            .setColor(0xffffff);
          const embed3s = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
          const pingRole = guild.roles.cache.get(PING_ROLE);
          const sessionCh = guild.channels.cache.get(SESSION_CHANNEL);
          if (!sessionCh || !pingRole) return interaction.followUp({ content: 'No session channel/ping role!', ephemeral: true });
          const m = await sessionCh.send({ content: pingRole.toString(), embeds: [embed1s, embed2s, embed3s] });
          sessionData.starterId = member.id;
          sessionData.startTime = Date.now();
          sessionData.startMsgId = m.id;
          
          // General ping voters
          const generalCh = guild.channels.cache.get(GENERAL_CHANNEL);
          if (generalCh) {
            let voterPings = '';
            const voteData = Object.values(sessionData.pendingVotes)[0];
            if (voteData && voteData.voters) {
              voterPings = voteData.voters.slice(0, 10).map(id => `<@${id}>`).join('\\n- ');
            }
            const generalEmbed = new EmbedBuilder()
              .setTitle(`${LCSRPC_EMOJI} | Session Management`)
              .setDescription(`> Join the session listed in <#${SESSION_CHANNEL}>, or face moderation!\\n- ${voterPings || 'Staff'}\\n\\n_See you ingame!_`)
              .setColor(0xffffff);
            generalCh.send({ embeds: [generalEmbed] });
          }
          
          // Create voice channels
          const parentCh = guild.channels.cache.get(SESSION_PARENT_CHANNEL);
          const parentCat = guild.channels.cache.get(SESSION_PARENT_CAT);
          if (parentCh && parentCat) {
            try {
              const divider = await guild.channels.create({
                name: '-------',
                type: ChannelType.GuildVoice,
                parent: parentCat.id,
                position: parentCh.position + 1,
                permissionOverwrites: [{ id: guild.id, deny: ['Connect', 'Speak', 'Stream', 'UseVoiceActivation'], allow: ['ViewChannel'] }]
              });

              const ingame = await guild.channels.create({
                name: 'In-Game: LCsRp',
                type: ChannelType.GuildVoice,
                parent: parentCat.id,
                position: divider.position + 1,
                permissionOverwrites: [{ id: guild.id, deny: ['Connect', 'Speak', 'Stream', 'UseVoiceActivation'], allow: ['ViewChannel'] }]
              });
              const players = await guild.channels.create({
                name: 'Players: 0/40',
                type: ChannelType.GuildVoice,
                parent: parentCat.id,
                position: ingame.position + 1,
                permissionOverwrites: [{ id: guild.id, deny: ['Connect', 'Speak', 'Stream', 'UseVoiceActivation'], allow: ['ViewChannel'] }]
              });
              sessionData.vcChannels = [divider.id, ingame.id, players.id];
              sessionData.playersVcId = players.id;
              // Update players every 2min
              const updateInterval = setInterval(async () => {
                const playersVc = guild.channels.cache.get(players.id);
                if (playersVc) {
                  const randomPlayers = Math.floor(Math.random() * 11);
                  await playersVc.setName(`Players: ${randomPlayers}/10`);
                }
              }, 300000); // 5min
              sessionData.vcUpdateInterval = updateInterval;
            } catch (e) {
              console.error('VC creation error:', e);
            }
          }
          
          // Schedule 1h DM
          const timer1 = setTimeout(async () => {
            await dmSessionCheck(guild, sessionData.starterId); // First to starter
          }, 3600000);
          sessionData.checkTimers.push(timer1);
          interaction.followUp({ content: 'Session started!', ephemeral: true });
          break;
        
        case 'session_boost':
          if (!isActive) return interaction.followUp({ content: 'No active session!', ephemeral: true });
          const pingRoleB = guild.roles.cache.get(PING_ROLE);
          const sessionChB = guild.channels.cache.get(SESSION_CHANNEL);
          if (!sessionChB || !pingRoleB) return interaction.followUp({ content: 'No channel/ping!', ephemeral: true });
          const embed1b = new EmbedBuilder().setImage(HEAD_IMG).setColor(0xffffff);
          const embed2b = new EmbedBuilder()
            .setDescription('The session is currently running **low** on players. Please join up to ensure that the server can be full!')
            .setColor(0xffffff);
          const embed3b = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
          await sessionChB.send({ content: `@here, ${pingRoleB.toString()}`, embeds: [embed1b, embed2b, embed3b] });
          await clearSession(guild, true); // Keep start embed
          interaction.followUp({ content: 'Low/boost posted!', ephemeral: true });
          break;
        
        case 'session_full':
          if (!isActive) return interaction.followUp({ content: 'No active session!', ephemeral: true });
          const sessionChF = guild.channels.cache.get(SESSION_CHANNEL);
          if (!sessionChF) return interaction.followUp({ content: 'No channel!', ephemeral: true });
          await sessionChF.send('The session has officially become full. Thank you so much for bringing up activity! \\n> There may be a queue in Liberty County State Roleplay Community (LCSRPC).');
          interaction.followUp({ content: 'Full alert posted!', ephemeral: true });
          break;
        
        case 'session_shutdown':
          if (!isActive) return interaction.followUp({ content: 'No active session!', ephemeral: true });
          const now = Date.now();
          if (sessionData.startTime && now - sessionData.startTime < 15 * 60 * 1000) {
            return interaction.followUp({ content: 'You are not permitted to shutdown a session unless 15 minutes has elapsed after the session started', ephemeral: true });
          }
          await clearSession(guild, false);
          await set_active(guild, false);
          const sessionChD = guild.channels.cache.get(SESSION_CHANNEL);
          if (sessionChD) {
            const embed1d = new EmbedBuilder().setDescription(`A session has been shut down by **${member.displayName}**. Thank you for joining today's session. See you soon!`).setColor(0xffffff);
            const embed2d = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
            await sessionChD.send({ embeds: [embed1d, embed2d] });
          }
          // Clear state/timers
          sessionData.starterId = null;
          sessionData.startTime = null;
          sessionData.startMsgId = null;
          sessionData.checkTimers.forEach(clearTimeout);
          sessionData.checkTimers = [];
          interaction.followUp({ content: 'Session shutdown!', ephemeral: true });
          break;
        
        default:
          interaction.followUp({ content: 'Invalid option', ephemeral: true });
      }
    }
    return;
  }
  
  if (interaction.isChatInputCommand()) {
    const { commandName } = interaction;

    // Channel check for economy slash
    if (!BOT_CHANNELS.includes(interaction.channel.id) && ['balance', 'bal', 'work', 'daily', 'leaderboard', 'lb'].includes(commandName)) {
      return interaction.reply({ content: 'Economy commands only in bot channels!', ephemeral: true });
    }

    if (commandName === 'sessions') {
      if (!MGMT_ROLES.some(id => interaction.member.roles.cache.has(id))) {
        return interaction.reply({ content: 'Only Management+ staff members of Liberty County State Roleplay Community are permitted to manage a session. Refrain from using this command again, unless you become Management.', ephemeral: true });
      }
      const guild = interaction.guild;
      const isActive = await getSessionActive(guild);
      const statusText = isActive ? 'The Session is **currently active**.' : 'The Session is **currently inactive**.';
      const optionsText = isActive 
        ? '> - 1. **Boost** the Session. \\n> - 2. **Shutdown** the Session. \\n> - 3. **Alert** that the Session is full.'
        : '> - 1. Initiate a Session **Vote**.\\n> - 2. **Start** a new Session.';
      
      const embed1 = new EmbedBuilder()
        .setImage(HEAD_IMG)
        .setColor(0xffffff);
      
      const embed2 = new EmbedBuilder()
        .setTitle(`${LCSRPC_EMOJI} | Session Management`)
        .setDescription(`> Welcome, ${interaction.member.toString()}. Thanks for opening Liberty County State Roleplay Community's Session Management panel.\\n\\n${statusText}\\n\\nPlease click the options below to manage the session further.\\n\\n${optionsText}`)
        .setColor(0xffffff);
      
      const embed3 = new EmbedBuilder()
        .setImage(FOOTER_IMG)
        .setColor(0xffffff);
      
      const options = isActive 
        ? [
            { label: 'Session Low/Boost', value: 'session_boost', description: 'Notify low players', emoji: '📈' },
            { label: 'Session Full', value: 'session_full', description: 'Alert full', emoji: '✅' },
            { label: 'Shutdown Session', value: 'session_shutdown', description: 'End session', emoji: '🔴' }
          ]
        : [
            { label: 'Start Session Vote', value: 'session_vote', description: 'Vote threshold modal', emoji: '📊' },
            { label: 'Start New Session', value: 'session_start', description: 'Ping start', emoji: '🟢' }
          ];
      
      const select = new StringSelectMenuBuilder()
        .setCustomId('session_menu')
        .setPlaceholder('Select session action...')
        .addOptions(options);
      
      const row = new ActionRowBuilder().addComponents(select);
      
      return interaction.reply({ embeds: [embed1, embed2, embed3], components: [row], ephemeral: false });
    }
    
    if (commandName === 'say') {
      if (!ADMIN_ROLES.some(id => interaction.member.roles.cache.has(id))) {
        return interaction.reply({ content: 'No!', ephemeral: true });
      }
      return interaction.reply(interaction.options.getString('msg'));
    }
    
    if (commandName === 'dmuser') {
      if (!ADMIN_ROLES.some(id => interaction.member.roles.cache.has(id))) {
        return interaction.reply({ content: 'Exec+ only!', ephemeral: true });
      }
      const uid = interaction.options.getString('uid').replace(/[<@!>]/g, '');
      const msg = interaction.options.getString('msg');
      try {
        const user = await client.users.fetch(uid).catch(() => null);
        if (!user) return interaction.reply({ content: 'Invalid user!', ephemeral: true });
        const embed = new EmbedBuilder()
          .setTitle('# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__')
          .setDescription(`> From **${interaction.user.displayName}**:\n> ${msg}\n-# Sent at ${new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`)
          .setColor(0x2b2d31);
        await user.send({ embeds: [embed] });
        interaction.reply({ content: 'DM sent!', ephemeral: true });
      } catch {
        interaction.reply({ content: 'Failed!', ephemeral: true });
      }
    }
    
    if (commandName === 'dmrole') {
      if (!interaction.member.roles.cache.has(LEADERSHIP_ROLE)) {
        return interaction.reply({ content: 'Leadership only!', ephemeral: true });
      }
      const rid = interaction.options.getString('rid').replace(/[<@&>]/g, '');
      const msg = interaction.options.getString('msg');
      const role = interaction.guild.roles.cache.get(rid);
      if (!role || role.members.size > 50) {
        return interaction.reply({ content: 'Too big/invalid!', ephemeral: true });
      }
      let count = 0;
      for (const member of role.members.values()) {
        if (member.user.bot) continue;
        const embed = new EmbedBuilder()
          .setTitle('# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__')
          .setDescription(`> From **${interaction.user.displayName}**:\n> ${msg}\n-# Sent at ${new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`)
          .setColor(0x2b2d31);
        try {
          await member.send({ embeds: [embed] });
          count++;
        } catch {}
      }
      interaction.reply({ content: `Sent to ${count}`, ephemeral: true });
    }
  }

  if (interaction.isButton()) {
    // Legacy buttons disabled - use dropdown
    return interaction.reply({ content: 'Use /sessions dropdown instead!', ephemeral: true });
  }

  if (interaction.isModalSubmit() && interaction.customId === 'vote_modal') {
    const t = parseInt(interaction.fields.getTextInputValue('threshold'));
    if (isNaN(t) || t < 1) {
      return interaction.reply({ content: 'Invalid number!', ephemeral: true });
    }
    const c = interaction.guild.channels.cache.get(VOTE_CHANNEL);
    if (!c) return interaction.reply({ content: 'No vote channel!', ephemeral: true });
    
    const embed1 = new EmbedBuilder().setImage(HEAD_IMG).setColor(0xffffff);
    const embed2 = new EmbedBuilder()
      .setTitle(`${LCSRPC_EMOJI} | LCSRPC Session Voting`)
      .setDescription(`> A session voting has been started by ${interaction.user.displayName}. \\n> - If you would like the session to start, please react below with <:Checkmark:${CHECKMARK_EMOJI}>. Once the session reaches ${t}, the session will begin. \\n> - Votes: 0/${t}`)
      .setColor(0xffffff);
    const embed3 = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
    
    const m = await c.send({ embeds: [embed1, embed2, embed3] });
    await m.react(`<:Checkmark:${CHECKMARK_EMOJI}>`);
    sessionData.pendingVotes[m.id] = { threshold: t, initiatorId: interaction.user.id };
    sessionData.voteMsgIds.push(m.id);
    interaction.reply({ content: 'Vote posted in staff-chat!', ephemeral: true });
  }
});

client.on('messageCreate', async message => {
  const BOT_ID = '1484655890966777886';
  if (message.mentions.has(client.user.id) || message.content.includes(`<@${BOT_ID}>`) || message.content.includes(`<@!${BOT_ID}>`)) {
    const guild = message.guild;
    const devUser = await guild.members.fetch('1261535675472281724').catch(() => null);
    const devNick = devUser ? devUser.displayName : 'Unknown';
    const embed = new EmbedBuilder()
      .setDescription(`> \`Prefix:\` **: **\n> \`Developer:\` **${devNick}**\n> \`Description:\` Maintaining ER:LC and Discord Systems for Liberty County State Roleplay Community (LCSRPC).\n> \`Last Deployed:\` <t:${Math.floor(Date.now() / 1000)}:R>`)
      .setColor(0xffffff);
    return message.reply({ embeds: [embed] });
  }
  const authorId = message.author.id;
  const guild = message.guild;
  
  // AFK check first
  if (afkUsers[authorId]) {
    const afkData = afkUsers[authorId];
    const member = guild.members.cache.get(authorId);
    if (member) {
      member.setNickname(afkData.oldNick).catch(console.error);
    }
    const pingsList = afkData.pings.map(id => `<@${id}>`).join(', ') || 'No one';
    const embedOff = new EmbedBuilder()
      .setTitle('**Back from AFK**')
      .setDescription(`**${message.member.displayName}**\n> You are back from AFK.\n> **Mentions while AFK:** ${pingsList}`)
      .setColor(0xffffff);
    message.reply({ embeds: [embedOff] }).catch(() => {});
    delete afkUsers[authorId];
    return; // Stop processing command
  }
  
  if (message.mentions.users.size > 0) {
    message.mentions.users.forEach(mentioned => {
      if (afkUsers[mentioned.id]) {
        const afkData = afkUsers[mentioned.id];
        message.reply(`\`${afkData.oldNick}\` is currently AFK: ${afkData.reason}`).catch(() => {});
        afkData.pings.push(message.author.id);
      }
    });
  }
  
  // AFK mentions check (after command processing)
  message.mentions.users.forEach(mentioned => {
    const mentionedId = mentioned.id;
    if (afkUsers[mentionedId]) {
      const afkData = afkUsers[mentionedId];
      message.channel.send(`\`${afkData.oldNick}\` is currently AFK: ${afkData.reason}`);
      afkData.pings.push(message.author.id);
    }
  });
  
  // Channel check for economy cmds only
  const command = message.content.slice(1).trim().split(/ +/)[0]?.toLowerCase();
  if (!BOT_CHANNELS.includes(message.channel.id) && ['bal', 'balance', 'work', 'daily', 'lb', 'leaderboard'].includes(command)) {
    message.delete().catch(() => {});
    const errorEmbed = new EmbedBuilder()
      .setDescription('Economy commands can only be used in **bot-cmds**, **economy**, or **staff-cmds** channels.')
      .setColor(0xff0000);
    const errorMsg = await message.channel.send({ embeds: [errorEmbed] });
    setTimeout(() => errorMsg.delete().catch(() => {}), 10000);
    return;
  }

  const args = message.content.slice(1).trim().split(/ +/);
  const cmd = args.shift()?.toLowerCase();

  if (cmd === 'sessions') {
    if (message.guild.id !== GUILD_ID || !MGMT_ROLES.some(id => message.member.roles.cache.has(id))) {
      const errorMsg = await message.reply('Only Management+ staff members of Liberty County State Roleplay Community are permitted to manage a session. Refrain from using this command again, unless you become Management.');
      setTimeout(() => {
        message.delete().catch(() => {});
        errorMsg.delete().catch(() => {});
      }, 5000);
      return;
    }
    const guild = message.guild;

    const isActive = await getSessionActive(guild);
    const statusText = isActive ? 'The Session is **currently active**.' : 'The Session is **currently inactive**.';
    const optionsText = isActive 
      ? '> - 1. **Boost** the Session. \\n> - 2. **Shutdown** the Session. \\n> - 3. **Alert** that the Session is full.'
      : '> - 1. Initiate a Session **Vote**.\\n> - 2. **Start** a new Session.';
    
    const embed1 = new EmbedBuilder()
      .setImage(HEAD_IMG)
      .setColor(0xffffff);
    
    const embed2 = new EmbedBuilder()
      .setTitle(`${LCSRPC_EMOJI} | Session Management`)
      .setDescription(`> Welcome, ${message.member.toString()}. Thanks for opening Liberty County State Roleplay Community's Session Management panel.\\n\\n${statusText}\\n\\nPlease click the options below to manage the session further.\\n\\n${optionsText}`)
      .setColor(0xffffff);
    
    const embed3 = new EmbedBuilder()
      .setImage(FOOTER_IMG)
      .setColor(0xffffff);
    
    const options = isActive 
      ? [
          { label: 'Session Low/Boost', value: 'session_boost', description: 'Notify low players', emoji: '📈' },
          { label: 'Session Full', value: 'session_full', description: 'Alert full', emoji: '✅' },
          { label: 'Shutdown Session', value: 'session_shutdown', description: 'End session', emoji: '🔴' }
        ]
      : [
          { label: 'Start Session Vote', value: 'session_vote', description: 'Vote threshold modal', emoji: '📊' },
          { label: 'Start New Session', value: 'session_start', description: 'Ping start', emoji: '🟢' }
        ];
    
    const select = new StringSelectMenuBuilder()
      .setCustomId('session_menu')
      .setPlaceholder('Select session action...')
      .addOptions(options);
    
    const row = new ActionRowBuilder().addComponents(select);
    
    await message.reply({ embeds: [embed1, embed2, embed3], components: [row] });
    await message.delete(); // Auto-delete command
  } else if (['bal', 'balance'].includes(cmd)) {
    const bal = await getBal(message.author.id);
    const embed = new EmbedBuilder()
      .setImage(ECON_HEADER_IMG)
      .setDescription(`**Balance:** $${bal.toLocaleString()}`)
      .setColor(0x00ff00);
    message.reply({ embeds: [embed] });
  } else if (cmd === 'work') {
    const cdKey = `work_${message.author.id}`;
    const now = Date.now();
    if (sessionData.cooldowns[cdKey] && now - sessionData.cooldowns[cdKey] < 3600000) {
      const remaining = Math.ceil((3600000 - (now - sessionData.cooldowns[cdKey])) / 60000);
      return message.reply(`Work on 1h cd. \`${remaining}m\` left.`);
    }
    sessionData.cooldowns[cdKey] = now;
    const reward = 50;
    const newBal = await addBal(message.author.id, reward, message.author.id);
    const embed = new EmbedBuilder()
      .setImage(ECON_HEADER_IMG)
      .setDescription(`**Worked! +$${reward}**\n**New Balance: $${newBal.toLocaleString()}**`)
      .setColor(0x00ff00);
    message.reply({ embeds: [embed] });
  } else if (cmd === 'daily') {
    const cdKey = `daily_${message.author.id}`;
    const now = Date.now();
    if (sessionData.cooldowns[cdKey] && now - sessionData.cooldowns[cdKey] < 86400000) {
      const remaining = Math.ceil((86400000 - (now - sessionData.cooldowns[cdKey])) / 60000);
      return message.reply(`Daily on 24h cd. \`${remaining}m\` left.`);
    }
    sessionData.cooldowns[cdKey] = now;
    const reward = 100;
    const newBal = await addBal(message.author.id, reward, message.author.id);
    const embed = new EmbedBuilder()
      .setImage(ECON_HEADER_IMG)
      .setDescription(`**Daily reward! +$${reward}**\n**New Balance: $${newBal.toLocaleString()}**`)
      .setColor(0x00ff00);
    message.reply({ embeds: [embed] });
  } else if (['lb', 'leaderboard'].includes(cmd)) {
    const sorted = Object.entries(economyData.users).sort(([,a], [,b]) => b - a).slice(0, 10);
    const lbList = sorted.map(([id, bal], i) => `\`${i+1}.\` <@${id}> $${bal.toLocaleString()}`).join('\\n');
    const embed = new EmbedBuilder()
      .setTitle('💰 Leaderboard')
      .setDescription(lbList || 'No balances yet.')
      .setColor(0x00ff88)
      .setImage(ECON_HEADER_IMG);
    message.reply({ embeds: [embed] });
  } else if (cmd === 'requesttraining') {
    const reqCh = client.channels.cache.get(TRAINING_REQ_CHANNEL);
    if (message.channel.id !== TRAINING_REQ_CHANNEL) {
      return message.reply('Training requests in <#' + TRAINING_REQ_CHANNEL + '> only!').then(m => setTimeout(() => m.delete(), 10000));
    }
    if (!await getSessionActive(message.guild)) {
      return message.reply('Session inactive!').then(m => setTimeout(() => m.delete(), 5000));
    }
    if (!BOD_EXEC_LEAD_ROLES.some(id => message.member.roles.cache.has(id)) && !message.member.roles.cache.has(TRAINEE_ROLE)) {
      return message.reply('BOD/Exec/Lead/trainee only!').then(m => setTimeout(() => m.delete(), 5000));
    }
    const trainerPing = message.guild.roles.cache.get(TRAINER_ROLE)?.toString() || '<@&1470596876662345790>';
    await message.delete();
    const reqEmbed1 = new EmbedBuilder().setImage(HEAD_IMG).setColor(0xffffff);
    const reqEmbed2 = new EmbedBuilder()
      .setTitle(`${LCSRPC_EMOJI} | Training Request`)
      .setDescription(`**${message.member.displayName}** requests training.\n> Session active. Assign trainer.`)
      .setColor(0xffffff);
    const reqEmbed3 = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
    message.channel.send({ content: `${trainerPing}`, embeds: [reqEmbed1, reqEmbed2, reqEmbed3] });
  } else if (cmd === 'afk') {
    const reason = args.join(' ') || 'AFK';
    const oldNick = message.member.displayName;
    afkUsers[message.author.id] = { reason, oldNick, pings: [] };
    message.member.setNickname(`${AFK_PREFIX}${reason.slice(0, 20)}`).catch(() => {});
    message.reply(`**AFK: ${reason}**`).then(m => setTimeout(() => m.delete(), 10000));
  }

  if (cmd === 'say') {
    if (message.guild.id !== GUILD_ID || !ADMIN_ROLES.some(id => message.member.roles.cache.has(id))) {
      return message.reply('No!').then(m => setTimeout(() => m.delete(), 5000));
    }
    const msg = args.join(' ');
    await message.delete();
    message.channel.send(msg);
  }

  if (cmd === 'dmuser') {
    if (message.guild.id !== GUILD_ID || !ADMIN_ROLES.some(id => message.member.roles.cache.has(id))) {
      return message.reply('No!').then(m => setTimeout(() => m.delete(), 5000));
    }
    const uid = args.shift().replace(/[<@!>]/g, '');
    const msgContent = args.join(' ');
    if (!msgContent) return message.reply('Usage: >dmuser user msg').then(m => setTimeout(() => m.delete(), 5000));
    await message.delete();
    try {
      const user = await client.users.fetch(uid).catch(() => null);
      if (!user) return message.reply('Invalid user!').then(m => setTimeout(() => m.delete(), 5000));
      const embed = new EmbedBuilder()
        .setTitle('# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__')
        .setDescription(`> From **${message.member.displayName}**:\n> ${msgContent}\n-# Sent at ${message.createdAt.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`)
        .setColor(0x2b2d31);
      await user.send({ embeds: [embed] });
      message.reply('DM sent!').then(m => setTimeout(() => m.delete(), 5000));
    } catch {
      message.reply('Failed!').then(m => setTimeout(() => m.delete(), 5000));
    }
  }

  if (cmd === 'dmrole') {
    if (message.guild.id !== GUILD_ID || !message.member.roles.cache.has(LEADERSHIP_ROLE)) {
      return message.reply('Leadership only!').then(m => setTimeout(() => m.delete(), 5000));
    }
    const rid = args.shift().replace(/[<@&>]/g, '');
    const msgContent = args.join(' ');
    if (!msgContent) return message.reply('Usage: >dmrole role msg').then(m => setTimeout(() => m.delete(), 5000));
    await message.delete();
    const role = message.guild.roles.cache.get(rid);
    if (!role || role.members.filter(m => !m.user.bot).size > 50) {
      return message.reply('Too big/invalid!').then(m => setTimeout(() => m.delete(), 5000));
    }
    let count = 0;
    for (const member of role.members.values()) {
      if (member.user.bot) continue;
      const embed = new EmbedBuilder()
        .setTitle('# <:Offical_server:1475860128686411837> __LCSRPC - New Direct Message (DM)__')
        .setDescription(`> From **${message.member.displayName}**:\n> ${msgContent}\n-# Sent at ${message.createdAt.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`)
        .setColor(0x2b2d31);
      try {
        await member.send({ embeds: [embed] });
        count++;
      } catch {}
    }
    message.reply(`DM sent to ${count}/${role.members.size}`).then(m => setTimeout(() => m.delete(), 5000));
  }
});

client.on('guildMemberAdd', member => {
  if (member.guild.id !== GUILD_ID) return;
  
  // Text welcome
  const textCh = client.channels.cache.get(WELCOME_TEXT);
  if (textCh) {
    const humanCount = member.guild.members.cache.filter(m => !m.user.bot).size;
    const ordinal = humanCount % 10 === 1 && humanCount % 100 !== 11 ? 'st' : humanCount % 10 === 2 && humanCount % 100 !== 12 ? 'nd' : humanCount % 10 === 3 && humanCount % 100 !== 13 ? 'rd' : 'th';
    const emojiBadge = '<:Welcome0:1484564259395604572><:Welcome1:1484564289309380780><:Welcome2:1484564315888681000><:Welcome3:1484564376995234037>';
    const msg = `${emojiBadge} **to Liberty County State Roleplay Community (LCSRPC), ${member.toString()}.** You are our \`${humanCount}${ordinal}\` member.\n> Thanks for joining, and have a wonderful day!`;
    textCh.send(msg);
  }
  
  // Embed welcome
  const embedCh = client.channels.cache.get(WELCOME_EMBED);
  if (embedCh) {
    embedCh.send(member.toString());
    const embed1 = new EmbedBuilder().setColor(0xffffff).setImage('https://cdn.discordapp.com/attachments/1484676715010588793/1484676770224410775/alrwelc.png?ex=69bf187d&is=69bdc6fd&hm=93aa43677dac68a2b37ac68dc12d7f151c4d45cdf9a7f976df3e9e88b17022d1&');
    const embed2 = new EmbedBuilder()
      .setTitle('**Welcome to Liberty County State!**')
      .setDescription(`> Thank you for joining LCSRPC, ${member.toString()}.\n\nLiberty County State Roleplay Community is an ER:LC private server, focused on the community surrounding Liberty County. Departments/Jobs are similar to the ER:LC counterparts, however reflect enhanced realism and roleplay. Liberty County State attempts to host sessions frequently throughout the week, ensuring activity to bring more fun.\n> 1. You must read our server-rules listed in <#1410039042938245163>.\n> 2. You must verify with our automation services in <#1470597322499952791>.\n> 3. In order to learn more about our community, please evaluate our <#1470597313343787030>.\n> 4. If you are ever in need of staff to answer any of your questions, you can create a **General Inquiry** ticket in <#1470597331551387702>.\n\nOtherwise, have a fantastic day, and we hope to see you interact with our community events, channels, and features.`);
    embedCh.send({ embeds: [embed1, embed2] });
  }
});

let economyData = { users: {}, logs: [] };

async function getBal(userId) {
  return economyData.users[userId] || 0;
}

async function addBal(userId, amt, logBy = null) {
  const bal = (economyData.users[userId] || 0) + amt;
  economyData.users[userId] = bal;
  if (logBy) {
    economyData.logs.unshift({
      type: amt > 0 ? 'add' : 'remove',
      userId,
      amt: Math.abs(amt),
      by: logBy,
      time: Date.now()
    });
  }
  return bal;
}

// Helper functions
async function getSessionActive(guild) {
  const statusVc = guild.channels.cache.get(SESSION_PARENT_CHANNEL);
  return statusVc ? statusVc.name.includes('🟢') : false;
}

async function getStaffCount(guild) {
  const staffRole = guild.roles.cache.get('1470596847423852758');
  return staffRole ? staffRole.members.filter(m => !m.user.bot).size : 0;
}

async function clearSession(guild, keepStartEmbed = false) {
  const c = guild.channels.cache.get(SESSION_CHANNEL);
  if (!c) return;
  try {
    const messages = await c.messages.fetch({ limit: 50 });
    const protectedMsg = PROTECTED_MSG;

    const startMsgId = sessionData.startMsgId;
    for (const msg of messages.values()) {
      if (msg.id !== protectedMsg && (!keepStartEmbed || msg.id !== startMsgId)) {
        await msg.delete().catch(() => {});
      }
    }
  } catch (e) {
    console.error('Clear session error:', e);
  }
}

async function dmSessionCheck(guild, targetId, first = false) {
  const target = await client.users.fetch(targetId).catch(() => null);
  if (!target) return;
  const embed1 = new EmbedBuilder().setImage(HEAD_IMG).setColor(0xffffff);
  const embed2 = new EmbedBuilder()
    .setTitle(`${LCSRPC_EMOJI} | Session Management`)
    .setDescription('As the session was started by you approximately an hour ago, please answer this question:\n> Is it currently still active?')
    .setColor(0xffffff);
  const embed3 = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
  const options = [
    { label: 'Yes', value: 'check_yes' },
    { label: 'No', value: 'check_no' }
  ];
  const select = new StringSelectMenuBuilder()
    .setCustomId(first ? 'starter_check' : 'mgmt_check')
    .setPlaceholder('Respond...')
    .addOptions(options);
  const row = new ActionRowBuilder().addComponents(select);
  await target.send({ embeds: [embed1, embed2, embed3], components: [row] });
  console.log(`DM check sent to ${target.tag}`);
  // Escalate stub: After 1h no resp, DM mgmt roles
  const escalateTimer = setTimeout(async () => {
    console.log('Escalating to mgmt roles');
    for (const roleId of MGMT_ROLES) {
      const role = guild.roles.cache.get(roleId);
      if (role) {
        role.members.fetch().then(members => {
          members.filter(m => !m.user.bot).forEach(async (mem) => {
            await dmSessionCheck(guild, mem.id, false);
          });
        });
      }
    }
  }, 3600000);
  sessionData.checkTimers.push(escalateTimer);
}

async function startSession(guild, starterId) {
  if (await getSessionActive(guild)) return console.log('Session already active');
  await clearSession(guild, false);
  await set_active(guild, true);
  const staffCount = await getStaffCount(guild);
  const embed1s = new EmbedBuilder().setImage(HEAD_IMG).setColor(0xffffff);
  const embed2s = new EmbedBuilder()
    .setTitle(`${LCSRPC_EMOJI} | LCSRPC Session Started`)
    .setDescription(`After votes received, a session has begun in Liberty County State Roleplay Community. Please refer below for more information.\n- **In-Game Code:** \`LCsRp\`\n- **Players:** 5/40\n- **Staff Online:** ${staffCount}`)
    .setColor(0xffffff);
  const embed3s = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
  const pingRole = guild.roles.cache.get(PING_ROLE);
  const sessionCh = guild.channels.cache.get(SESSION_CHANNEL);
  if (!sessionCh || !pingRole) return;
  const m = await sessionCh.send({ content: pingRole.toString(), embeds: [embed1s, embed2s, embed3s] });
  sessionData.starterId = starterId;
  sessionData.startTime = Date.now();
  sessionData.startMsgId = m.id;
  const timer1 = setTimeout(() => dmSessionCheck(guild, starterId, true), 3600000);
  sessionData.checkTimers.push(timer1);
  console.log('Session started, DM timer set');
}

async function shutdownSession(guild) {
  await clearSession(guild, false);
  
  // Delete VC
  if (sessionData.vcChannels) {
    for (const vcId of sessionData.vcChannels) {
      const vc = guild.channels.cache.get(vcId);
      if (vc) await vc.delete().catch(console.error);
    }
  }
  if (sessionData.vcUpdateInterval) {
    clearInterval(sessionData.vcUpdateInterval);
  }
  
  await set_active(guild, false);
  const sessionChD = guild.channels.cache.get(SESSION_CHANNEL);
  if (sessionChD) {
    const embed1d = new EmbedBuilder().setDescription("A session has been shut down automatically. Thank you for joining today's session. See you soon!").setColor(0xffffff);
    const embed2d = new EmbedBuilder().setImage(FOOTER_IMG).setColor(0xffffff);
    await sessionChD.send({ embeds: [embed1d, embed2d] });
  }
  sessionData.starterId = null;
  sessionData.startTime = null;
  sessionData.startMsgId = null;
  sessionData.vcChannels = null;
  sessionData.playersVcId = null;
  sessionData.vcUpdateInterval = null;
  sessionData.checkTimers.forEach(t => clearTimeout(t));
  sessionData.checkTimers = [];
  console.log('Session auto-shutdown + VC cleaned');
}

// Helper functions (called from events)
async function set_active(guild, active) {
  const statusVc = guild.channels.cache.get(SESSION_PARENT_CHANNEL);
  if (statusVc) await statusVc.setName(active ? 'Sessions: 🟢' : 'Sessions: 🔴');
}

client.on('messageReactionAdd', async (reaction, user) => {
  if (user.bot || reaction.emoji.id !== CHECKMARK_EMOJI) return;
  const msgId = reaction.message.id;
  const data = sessionData.pendingVotes[msgId];
  if (!data) return;
  const checkReact = reaction.message.reactions.cache.get(`<:Checkmark:${CHECKMARK_EMOJI}>`);
  const count = (checkReact ? checkReact.count : 0) - 1;
  if (count >= data.threshold) {
    console.log('Vote threshold reached, auto-starting session');
    await startSession(reaction.message.guild, data.initiatorId);
    delete sessionData.pendingVotes[msgId];
  }
});

client.on('messageReactionRemove', async (reaction, user) => {
  if (user.bot || reaction.emoji.id !== CHECKMARK_EMOJI) return;
  const msgId = reaction.message.id;
  const data = sessionData.pendingVotes[msgId];
  if (!data) return;
  // Optional: Clean if count == 0
});

client.on('error', err => console.error('Discord Client Error:', err));
client.on('warn', info => console.warn('Discord Client Warn:', info));
client.on('shardDisconnect', (event, code) => console.log('Shard Disconnect:', code));

setInterval(() => {
  if (client.isReady()) {
    client.user.setPresence({ 
      activities: [{ name: 'Liberty County | dsc.gg/lcsrpc', type: 3 }], 
      status: 'online' 
    });
    console.log('Presence updated');
  }
}, 30000);

client.login(token);
