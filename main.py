import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import Optional
import datetime

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Centralized Data Storage
server_data = {
    "anti_link": {"enabled": False, "blocked_list": []},
    "bad_words": [],
    "welcome": {
        "channel_id": None,
        "title": "Welcome to our Server!",
        "description": "Welcome {member}!",
        "image_url": None,
        "color": 0x00ff00
    },
    "leave": {
        "channel_id": None,
        "title": "Goodbye from the Server!",
        "description": "{member} has left us. We will miss you!",
        "image_url": None,
        "color": 0xff0000
    }
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Syncing slash commands to Discord
        await self.tree.sync()
        print(f"✅ Slash commands synced for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 Logged in as {bot.user.name}')
    print(f'🛡️ Security Systems: Active')

# ================= WELCOME & LEAVE EVENTS =================

@bot.event
async def on_member_join(member):
    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            join_date = member.joined_at.strftime("%d-%m-%Y")
            desc = config["description"].replace("{member}", member.mention)
            desc += f"\n\n🏟️ **Server:** {member.guild.name}\n📅 **Joined At:** {join_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member Count: #{member.guild.member_count}")
            await channel.send(content=f"Welcome {member.mention}!", embed=embed)

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            leave_date = datetime.datetime.now().strftime("%d-%m-%Y")
            desc = config["description"].replace("{member}", f"**{member.name}**")
            desc += f"\n\n🏟️ **Server:** {member.guild.name}\n📤 **Left On:** {leave_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

# ================= MODALS FOR CUSTOMIZATION =================

class WelcomeSetupModal(Modal, title="Customize Welcome"):
    title_in = TextInput(label="Welcome Title", default="Welcome!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="Welcome {member}!")
    gif_in = TextInput(label="Image/GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("✅ Welcome updated!", ephemeral=True)

class LeaveSetupModal(Modal, title="Customize Leave"):
    title_in = TextInput(label="Leave Title", default="Goodbye!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="{member} left.")
    gif_in = TextInput(label="Image/GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["leave"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("✅ Leave updated!", ephemeral=True)

# ================= MODERATION & SECURITY COMMANDS =================

@bot.tree.command(name="addword", description="Add a word to the bad words blocklist")
@app_commands.checks.has_permissions(administrator=True)
async def addword(interaction: discord.Interaction, word: str):
    word = word.lower()
    if word not in server_data["bad_words"]:
        server_data["bad_words"].append(word)
        await interaction.response.send_message(f"✅ `{word}` is now blocked.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Word already exists in list.", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Configure Welcome system")
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.success)
    async def cb(i): await i.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Welcome channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Configure Leave system")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.danger)
    async def cb(i): await i.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Leave channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="antilink", description="Enable/Disable Anti-Link")
@app_commands.checks.has_permissions(administrator=True)
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    status = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
    await interaction.response.send_message(f"🛡️ Anti-Link is now **{status}**", ephemeral=True)

@bot.tree.command(name="lock", description="Lock this channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(description="🔒 **Channel Locked**", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unlock", description="Unlock this channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(description="🔓 **Channel Unlocked**", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Cleared {len(deleted)} messages.")

# ================= AUTO-MODERATION LOGIC =================



@bot.event
async def on_message(message):
    if message.author.bot: return

    content = message.content.lower()

    # 1. Bad Words Filter
    for word in server_data["bad_words"]:
        if word in content:
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Restricted Content", description=f"{message.author.mention}, your message contained prohibited words.", color=discord.Color.red())
                await message.channel.send(embed=embed, delete_after=5)
                return 
            except: pass

    # 2. Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        if "http" in content or "discord.gg" in content or ".com" in content:
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Link Blocked", description=f"{message.author.mention}, sending links is restricted here.", color=discord.Color.orange())
                await message.channel.send(embed=embed, delete_after=5)
                return
            except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(description="🔓 This channel has been **Unlocked**.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Delete a certain amount of messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    embed = discord.Embed(description=f"🧹 Successfully cleared **{len(deleted)}** messages.", color=discord.Color.green())
    await interaction.followup.send(embed=embed)

# ================= SECURITY LOGIC (Unique Embed Warnings) =================

@bot.event
async def on_message(message):
    if message.author.bot: return

    msg_content = message.content.lower()

    # 1. Bad Words Filter
    for word in server_data["bad_words"]:
        if word in msg_content:
            try:
                await message.delete()
                embed = discord.Embed(
                    title="🚫 Profanity Detected",
                    description=f"{message.author.mention}, your message contained prohibited words.",
                    color=discord.Color.from_rgb(255, 0, 0)
                )
                await message.channel.send(embed=embed, delete_after=5)
                return 
            except: pass

    # 2. Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        is_link = "http" in msg_content or "discord.gg" in msg_content or ".com" in msg_content
        if is_link:
            try:
                await message.delete()
                embed = discord.Embed(
                    title="🚫 Link Restricted",
                    description=f"{message.author.mention}, you are not allowed to send links.",
                    color=discord.Color.from_rgb(255, 87, 51)
                )
                await message.channel.send(embed=embed, delete_after=5)
                return
            except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
    await interaction.followup.send(embed=embed)

# ================= SECURITY LOGIC (Embed Warnings) =================

@bot.event
async def on_message(message):
    if message.author.bot: return

    # 1. Bad Words Filter
    msg_content = message.content.lower()
    for word in server_data["bad_words"]:
        if word in msg_content:
            try:
                await message.delete()
                embed = discord.Embed(
                    title="🚫 Profanity Detected",
                    description=f"{message.author.mention}, your message contained prohibited words and has been removed.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=5)
                return 
            except: pass

    # 2. Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        is_link = "http" in msg_content or "discord.gg" in msg_content or ".com" in msg_content
        if is_link:
            try:
                await message.delete()
                embed = discord.Embed(
                    title="🚫 Link Restricted",
                    description=f"{message.author.mention}, sending links is not allowed in this server.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=5)
                return
            except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
