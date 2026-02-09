import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import Optional
import datetime

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Data Storage (Note: This resets on Railway restart)
server_data = {
    "anti_link": {"enabled": False},
    "bad_words": [],
    "auto_role_id": None,
    "afk_users": {},
    "welcome": {"channel_id": None, "title": "Welcome!", "description": "Welcome {member}!", "image_url": None, "color": 0x00ff00},
    "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "color": 0xff0000}
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Slash Commands Synced")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is online!')

# ================= FIXED ON_MESSAGE (CRASH PROOF) =================

@bot.event
async def on_message(message):
    # Ignore bots and DMs to prevent errors
    if message.author.bot or not message.guild:
        return

    try:
        # 1. AFK REMOVAL
        if message.author.id in server_data["afk_users"]:
            del server_data["afk_users"][message.author.id]
            await message.channel.send(f"Welcome back {message.author.mention}!", delete_after=5)

        # 2. AFK MENTION CHECK
        if message.mentions:
            for mentioned in message.mentions:
                if mentioned.id in server_data["afk_users"]:
                    reason = server_data["afk_users"][mentioned.id]
                    await message.reply(f"📌 {mentioned.name} is AFK: {reason}", delete_after=10)

        # 3. SECURITY FILTERS (Bad Words & Links)
        msg_content = message.content.lower()
        
        # Check Bad Words
        for word in server_data["bad_words"]:
            if word in msg_content:
                await message.delete()
                return # Stop processing further if deleted

        # Check Anti-Link
        if server_data["anti_link"]["enabled"]:
            if any(x in msg_content for x in ["http", "discord.gg", ".com"]):
                await message.delete()
                return

    except Exception as e:
        print(f"⚠️ Event Error: {e}") # Log the error but don't stop the bot

    await bot.process_commands(message)

# ================= ALL COMMANDS INCLUDED =================

@bot.tree.command(name="afk", description="Set AFK status")
async def afk(interaction: discord.Interaction, reason: str = "Away"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"✅ AFK set: {reason}")

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message("❌ Role hierarchy error!", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member.name}")

@bot.tree.command(name="unban", description="Unban via ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ Unbanned {user.name}")

@bot.tree.command(name="lock", description="Lock channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Locked.")

@bot.tree.command(name="unlock", description="Unlock channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Unlocked.")

@bot.tree.command(name="clear", description="Delete messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {amount} messages.")

@bot.tree.command(name="setup_welcome", description="Setup Welcome")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    await interaction.response.send_message(f"📍 Welcome channel: {channel.mention}")

@bot.tree.command(name="antilink", description="Toggle Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"🛡️ Anti-Link: {'ON' if server_data['anti_link']['enabled'] else 'OFF'}")

@bot.tree.command(name="addword", description="Block a word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Blocked: {word}")

bot.run(TOKEN)
