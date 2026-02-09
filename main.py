import os
import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Data Storage
server_data = {
    "anti_link": {"enabled": False},
    "bad_words": [],
    "auto_role_id": None,
    "afk_users": {},
    "welcome": {"channel_id": None, "title": "Welcome!", "description": "Welcome {member} to our server!", "image": None},
    "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} has left us."}
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ All Commands Synced for {self.user.name}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 Bot is Online!')

# ================= EVENTS (Welcome, Leave, Auto-Role) =================

@bot.event
async def on_member_join(member):
    # Auto-Role logic
    if server_data["auto_role_id"]:
        role = member.guild.get_role(server_data["auto_role_id"])
        if role:
            try: await member.add_roles(role)
            except: pass

    # Welcome message
    cfg = server_data["welcome"]
    if cfg["channel_id"]:
        ch = bot.get_channel(cfg["channel_id"])
        if ch:
            emb = discord.Embed(title=cfg["title"], description=cfg["description"].replace("{member}", member.mention), color=0x2ecc71)
            if cfg["image"]: emb.set_image(url=cfg["image"])
            await ch.send(embed=emb)

@bot.event
async def on_member_remove(member):
    cfg = server_data["leave"]
    if cfg["channel_id"]:
        ch = bot.get_channel(cfg["channel_id"])
        if ch:
            emb = discord.Embed(title=cfg["title"], description=cfg["description"].replace("{member}", member.name), color=0xe74c3c)
            await ch.send(embed=emb)

# ================= AFK & SECURITY LOGIC =================

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # AFK Logic
    if message.author.id in server_data["afk_users"]:
        del server_data["afk_users"][message.author.id]
        await message.channel.send(f"Welcome back {message.author.mention}, AFK removed!", delete_after=5)

    if message.mentions:
        for m in message.mentions:
            if m.id in server_data["afk_users"]:
                await message.reply(f"📌 {m.name} is AFK: {server_data['afk_users'][m.id]}", delete_after=10)

    # Anti-link & Bad-words logic
    msg = message.content.lower()
    if server_data["anti_link"]["enabled"] and any(x in msg for x in ["http", "discord.gg", ".com"]):
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            return

    for word in server_data["bad_words"]:
        if word in msg:
            await message.delete()
            return

    await bot.process_commands(message)

# ================= MODERATION COMMANDS =================

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member.name}")

@bot.tree.command(name="unban", description="Unban a user by ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ Unbanned {user.name}")

@bot.tree.command(name="timeout", description="Mute/Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration)
    await interaction.response.send_message(f"⏳ {member.name} timed out for {minutes} minutes.")

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Cleared {amount} messages.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel Locked.")

@bot.tree.command(name="unlock", description="Unlock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel Unlocked.")

# ================= SECURITY & UTILITY COMMANDS =================

@bot.tree.command(name="antilink", description="Toggle Anti-Link filter")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    state = "ON" if server_data["anti_link"]["enabled"] else "OFF"
    await interaction.response.send_message(f"🛡️ Anti-Link is now **{state}**")

@bot.tree.command(name="addword", description="Block a specific word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Word `{word}` has been blacklisted.")

@bot.tree.command(name="afk", description="Set AFK status")
async def afk(interaction: discord.Interaction, reason: str = "Away"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"✅ {interaction.user.mention} is now AFK: {reason}")

@bot.tree.command(name="setup_welcome", description="Set welcome channel")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}")

@bot.tree.command(name="setup_autorole", description="Set auto-role for new members")
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    server_data["auto_role_id"] = role.id
    await interaction.response.send_message(f"✅ Auto-Role set to: {role.name}")

bot.run(TOKEN)
