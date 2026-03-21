const { Client, GatewayIntentBits, EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, ModalBuilder, TextInputBuilder, TextInputStyle, ChannelType } = require('discord.js');
const express = require('express');
const path = require('path');

const client = new Client({ 
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent] 
});

const token = process.env.BOT_TOKEN;
const GUILD_ID = '1289789596238086194';
const SESSION_CHANNEL = '1470597340992901204';
const VOTE_CHANNEL = '1471995054238208223';
const NAME_CHANNEL = '1480013219199451308';
const PROTECTED_MSG = '1480023088799416451';
const WELCOME_TEXT = '1470597378116681812';
const WELCOME_EMBED = '1470941203343216843';
const PING_ROLE = '1470597003292573787';
const CHECKMARK_EMOJI = '1480018743714386070';

const MGMT_ROLES = ['1470596840369164288', '1470596832794251408', '1470596825575854223', '1470596818298601567'];
const ADMIN_ROLES = ['1470596825575854223', '1470596832794251408', '1470596818298601567'];
const LEADERSHIP_ROLE = '1470596818298601567';

let sessionData = { active: false, cooldowns: {}, pendingVotes: {} };

const app = express();
app.use(express.json());
app.get('/', (req, res) => res.json({ status: 'alive' }));
app.get('/status', (req, res) => res.json({ status: 'alive', bot: client.isReady() ? 'ready' : 'starting' }));

const port = process.env.PORT || 5000;
app.listen(port, '0.0.0.0', () => console.log(`Flask on port ${port}`));

client.once('ready', () => {
  console.log(`${client.user.tag} ready!`);
  client.user.setPresence({ activities: [{ name: 'Liberty County | dsc.gg/lcsrpc', type: 3 }] });
});

client.on('interactionCreate', async interaction => {
  if (!interaction.isChatInputCommand() && !interaction.isButton() && !interaction.isModalSubmit()) return;
  
  if (interaction.isChatInputCommand()) {
    const { commandName } = interaction;
    
    if (commandName === 'sessions') {
      if (!MGMT_ROLES.some(id => interaction.member.roles.cache.has(id))) {
        return interaction.reply({ content: 'Mgmt+, Directors, Exec, Leadership only!', ephemeral: true });
      }
      const embed = new EmbedBuilder().setTitle('Sessions Panel').setDescription(`Active: ${sessionData.active}`).setColor(0xffffff);
      const view = new ActionRowBuilder().addComponents(
        new ButtonBuilder().setCustomId('vote').setLabel('Vote').setStyle(ButtonStyle.Primary),
        new ButtonBuilder().setCustomId('start').setLabel('Start').setStyle(ButtonStyle.Success),
        new ButtonBuilder().setCustomId('boost').setLabel('Boost').setStyle(ButtonStyle.Secondary),
        new ButtonBuilder().setCustomId('shutdown').setLabel('Shutdown').setStyle(ButtonStyle.Danger),
        new ButtonBuilder().setCustomId('full').setLabel('Full').setStyle(ButtonStyle.Danger)
      );
      return interaction.reply({ embeds: [embed], components: [view], ephemeral: true });
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
    if (!MGMT_ROLES.some(id => interaction.member.roles.cache.has(id))) {
      return interaction.reply({ content: 'Mgmt+ only!', ephemeral: true });
    }

    const id = interaction.customId;
    const guild = interaction.guild;
    const pingRole = guild.roles.cache.get(PING_ROLE);
    const sessionCh = guild.channels.cache.get(SESSION_CHANNEL);

    if (id === 'vote') {
      const modal = new ModalBuilder()
        .setCustomId('vote_modal')
        .setTitle('Vote Threshold');
      const input = new TextInputBuilder()
        .setCustomId('threshold')
        .setLabel('Votes needed')
        .setStyle(TextInputStyle.Short)
        .setPlaceholder('5');
      modal.addComponents(new ActionRowBuilder().addComponents(input));
      return interaction.showModal(modal);
    }

    if (id === 'start' && !sessionData.active && sessionCh && pingRole) {
      sessionData.active = true;
      set_active(guild, true);
      clear_session(guild);
      const embed = new EmbedBuilder().setTitle('Session Started').setDescription('LCsRp').setColor('00ff00');
      sessionCh.send({ content: pingRole.toString(), embeds: [embed] });
      interaction.reply({ content: 'Started!', ephemeral: true });
    }

    if (id === 'boost' && sessionData.active && sessionCh && pingRole) {
      const embed = new EmbedBuilder().setTitle('Boost').setDescription('Join!').setColor(0x5865f2);
      sessionCh.send({ content: pingRole.toString(), embeds: [embed] });
      interaction.reply({ content: 'Boosted!', ephemeral: true });
    }

    if (id === 'shutdown' && sessionData.active && sessionCh) {
      const now = Date.now();
      if (sessionData.cooldowns.shutdown && now - sessionData.cooldowns.shutdown < 15 * 60 * 1000) {
        return interaction.reply({ content: 'Cooldown!', ephemeral: true });
      }
      sessionData.active = false;
      set_active(guild, false);
      clear_session(guild);
      const embed = new EmbedBuilder().setTitle('Shutdown').setDescription('Ended').setColor('ff0000');
      sessionCh.send({ embeds: [embed] });
      sessionData.cooldowns.shutdown = now;
      interaction.reply({ content: 'Shutdown!', ephemeral: true });
    }

    if (id === 'full' && sessionData.active && sessionCh && pingRole) {
      const embed = new EmbedBuilder().setTitle('Full').setDescription('Full!').setColor('ff0000');
      sessionCh.send({ content: pingRole.toString(), embeds: [embed] });
      interaction.reply({ content: 'Full!', ephemeral: true });
    }
  }

  if (interaction.isModalSubmit() && interaction.customId === 'vote_modal') {
    const t = parseInt(interaction.fields.getTextInputValue('threshold'));
    if (isNaN(t)) {
      return interaction.reply({ content: 'Invalid number!', ephemeral: true });
    }
    const c = interaction.guild.channels.cache.get(VOTE_CHANNEL);
    if (!c) return;
    const embed = new EmbedBuilder().setTitle('Vote').setDescription(`React <:Checkmark:${CHECKMARK}> (${t} needed)`).setColor(0xffffff);
    const m = await c.send({ embeds: [embed] });
    await m.react(`<:${'Checkmark'}:${CHECKMARK}>`);
    sessionData.pendingVotes[m.id] = t;
    interaction.reply({ content: 'Vote posted!', ephemeral: true });
  }
});

client.on('messageCreate', async message => {
  if (message.author.bot || !message.content.startsWith('>')) return;
  
  const args = message.content.slice(1).trim().split(/ +/);
  const command = args.shift().toLowerCase();

  if (command === 'sessions') {
    if (message.guild.id !== GUILD_ID || !MGMT_ROLES.some(id => message.member.roles.cache.has(id))) {
      return message.reply('Mgmt+, Directors, Exec, Leadership only!').then(m => setTimeout(() => m.delete(), 5000));
    }
    const embed = new EmbedBuilder().setTitle('Sessions Panel').setDescription(`Active: ${sessionData.active}`).setColor(0xffffff);
    const view = [new ActionRowBuilder().addComponents(
      new ButtonBuilder().setCustomId('vote').setLabel('Vote').setStyle(ButtonStyle.Primary),
      new ButtonBuilder().setCustomId('start').setLabel('Start').setStyle(ButtonStyle.Success),
      new ButtonBuilder().setCustomId('boost').setLabel('Boost').setStyle(ButtonStyle.Secondary),
      new ButtonBuilder().setCustomId('shutdown').setLabel('Shutdown').setStyle(ButtonStyle.Danger),
      new ButtonBuilder().setCustomId('full').setLabel('Full').setStyle(ButtonStyle.Danger)
    )];
    await message.reply({ embeds: [embed], components: view });
  }

  if (command === 'say') {
    if (message.guild.id !== GUILD_ID || !ADMIN_ROLES.some(id => message.member.roles.cache.has(id))) {
      return message.reply('No!').then(m => setTimeout(() => m.delete(), 5000));
    }
    const msg = args.join(' ');
    await message.delete();
    message.channel.send(msg);
  }

  if (command === 'dmuser') {
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

  if (command === 'dmrole') {
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
    const msg = `${emojiBadge} ** to Liberty County State Roleplay Community (LCSRPC), ${member.toString()}.** You are our \`${humanCount}${ordinal}\` member. > Thanks for joining, and have a wonderful day!`;
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

// Helper functions (called from events)
async function set_active(guild, active) {
  const c = guild.channels.cache.get(NAME_CHANNEL);
  if (c) await c.setName(active ? '🟢 Sessions' : '🔴 Sessions');
}

async function clear_session(guild) {
  const c = guild.channels.cache.get(SESSION_CHANNEL);
  if (!c) return;
  try {
    const messages = await c.messages.fetch({ limit: 50 });
    for (const msg of messages.values()) {
      if (msg.id !== PROTECTED_MSG) {
        await msg.delete().catch(() => {});
      }
    }
  } catch {}
}

client.login(token);
