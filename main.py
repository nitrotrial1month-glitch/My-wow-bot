import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from typing import Optional
import datetime
import asyncio

# Railway Environment Variable
TOKEN = os.getenv('DISCORD_TOKEN')

# Centralized Data Structure
server_data = {
    "anti_link": {"enabled": False},
    "bad_words": [],
    "auto_role_id": None,
    "afk_users": {},
    "ticket_count": 0,
    "ticket_dashboard": {
        "title": "Support Center",
        "description": "Please select a category below to open a ticket.",
        "image": "https://i.imgur.com/vHq49Yj.png"
    },
    "ticket_inside": {
        "title": "Support Ticket",
        "description": "Hello {member}, our support team will be with you shortly. Please describe your issue.",
        "color": 0x3498db
    },
    "welcome": {
        "channel_id": None,
        "title": "Welcome!",
        "description": "Welcome {member} to the server!",
        "image_url": None,
        "color": 0x2ecc71
    },
    "leave": {
        "channel_id": None,
        "title": "Goodbye!",
        "description": "{member} has left the server.",
        "image_url": None,
        "color": 0xe74c3c
    }
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Persistent Views Registration
        self.add_view(TicketLauncher())
        self.add_view(TicketControl())
        await self.tree.sync()
        print(f"✅ Syncing successful!")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is now Online!')

# ================= EVENTS (Welcome, Leave, Security, AFK) =================

@bot.event
async def on_member_join(member):
    # Auto-Role
    if server_data["auto_role_id"]:
        role = member.guild.get_role(server_data["auto_role_id"])
        if role: await member.add_roles(role)

    # Welcome Message
    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            embed = discord.Embed(title=config["title"], description=config["description"].replace("{member}", member.mention), color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            embed = discord.Embed(title=config["title"], description=config["description"].replace("{member}", member.name), color=config["color"])
            await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # AFK Logic
    if message.author.id in server_data["afk_users"]:
        del server_data["afk_users"][message.author.id]
        await message.channel.send(f"Welcome back {message.author.mention}, your AFK status is removed.", delete_after=5)

    if message.mentions:
        for user in message.mentions:
            if user.id in server_data["afk_users"]:
                await message.reply(f"📌 {user.name} is currently AFK: {server_data['afk_users'][user.id]}", delete_after=10)

    # Security: Anti-Link & Bad Words
    content = message.content.lower()
    if server_data["anti_link"]["enabled"] and any(x in content for x in ["http://", "https://", "discord.gg/"]):
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            return await message.channel.send(f"🚫 {message.author.mention}, links are not allowed!", delete_after=5)

    for word in server_data["bad_words"]:
        if word in content:
            await message.delete()
            return await message.channel.send(f"🚫 {message.author.mention}, watch your language!", delete_after=5)

    await bot.process_commands(message)

# ================= TICKET UI COMPONENTS =================

class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="persistent_close")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ This channel will be deleted in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="persistent_claim")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Only staff can claim tickets.", ephemeral=True)
        await interaction.response.send_message(f"✅ Ticket claimed by {interaction.user.mention}", ephemeral=False)
        self.claim.disabled = True
        await interaction.message.edit(view=self)

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", description="For general queries", emoji="🛠️"),
            discord.SelectOption(label="Report Member", description="Report rule violations", emoji="🚫")
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options, custom_id="persistent_drop")

    async def callback(self, interaction: discord.Interaction):
        server_data["ticket_count"] += 1
        num = server_data["ticket_count"]
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="TICKETS")
        if not category: category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=f"ticket-{num}", category=category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

        config = server_data["ticket_inside"]
        embed = discord.Embed(title=config["title"], description=config["description"].replace("{member}", interaction.user.mention), color=discord.Color.blue())
        await channel.send(embed=embed, view=TicketControl())

class TicketLauncher(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ================= SLASH COMMANDS (ALL CATEGORIES) =================

# --- Moderation ---
@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Cleared {amount} messages.", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member.name}.")

@bot.tree.command(name="timeout", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration)
    await interaction.response.send_message(f"⏳ {member.name} timed out for {minutes}m.")

# --- Security ---
@bot.tree.command(name="antilink", description="Toggle Anti-Link protection")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    state = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
    await interaction.response.send_message(f"🛡️ Anti-Link is now **{state}**.")

@bot.tree.command(name="addword", description="Blacklist a word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Word `{word}` added to blacklist.")

# --- Ticket System ---
@bot.tree.command(name="ticket_setup", description="Deploy Ticket Panel")
async def ticket_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    config = server_data["ticket_dashboard"]
    embed = discord.Embed(title=config["title"], description=config["description"], color=0x2ecc71)
    if config["image"]: embed.set_image(url=config["image"])
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message("✅ Ticket Panel deployed.", ephemeral=True)

# --- Utility & AFK ---
@bot.tree.command(name="afk", description="Set AFK status")
async def afk(interaction: discord.Interaction, reason: str = "Away from keyboard"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"✅ You are now AFK: {reason}")

@bot.tree.command(name="setup_welcome", description="Configure Welcome Channel")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}")

bot.run(TOKEN)
