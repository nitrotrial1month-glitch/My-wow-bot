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
        await self.tree.sync()
        print(f"✅ Synced Slash Commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is online and secured!')

# ================= WELCOME & LEAVE =================

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
            await channel.send(content=f"Hey {member.mention}, Welcome!", embed=embed)

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            join_date = member.joined_at.strftime("%d-%m-%Y") if member.joined_at else "Unknown"
            leave_date = datetime.datetime.now().strftime("%d-%m-%Y")
            desc = config["description"].replace("{member}", f"**{member.name}**")
            desc += f"\n\n🏟️ **Server:** {member.guild.name}\n📥 **Joined:** {join_date}\n📤 **Left:** {leave_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="User Left the Server")
            await channel.send(embed=embed)

# ================= MODALS =================

class WelcomeSetupModal(Modal, title="Customize Welcome"):
    title_in = TextInput(label="Welcome Title", default="Welcome to the Server!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="Welcome {member}!")
    gif_in = TextInput(label="Image/GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("✅ Welcome settings updated!", ephemeral=True)

class LeaveSetupModal(Modal, title="Customize Leave"):
    title_in = TextInput(label="Leave Title", default="Goodbye!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="{member} just left us.")
    gif_in = TextInput(label="Image/GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["leave"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("✅ Leave settings updated!", ephemeral=True)

# ================= COMMANDS =================

@bot.tree.command(name="addword", description="Add a word to the bad words list")
@app_commands.checks.has_permissions(administrator=True)
async def addword(interaction: discord.Interaction, word: str):
    word = word.lower()
    if word not in server_data["bad_words"]:
        server_data["bad_words"].append(word)
        await interaction.response.send_message(f"✅ Word `{word}` added to blocklist.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ This word is already in the list.", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Setup the welcome system")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Customize Welcome", style=discord.ButtonStyle.success)
    async def cb(i): await i.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Welcome channel set to: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Setup the leave system")
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Customize Leave", style=discord.ButtonStyle.danger)
    async def cb(i): await i.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Leave channel set to: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="antilink", description="Enable or Disable Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    status = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
    embed = discord.Embed(description=f"🛡️ Anti-Link Security is now **{status}**.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="blocklink", description="Block a specific link")
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked_list"].append(link.lower())
    await interaction.response.send_message(f"✅ Link `{link}` added to blocklist.", ephemeral=True)

@bot.tree.command(name="clear", description="Delete a certain amount of messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    embed = discord.Embed(description=f"🧹 Successfully cleared **{len(deleted)}** messages.", color=discord.Color.green())
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
