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
    "auto_role_id": None, # Stores the ID of the role to be given automatically
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
        print(f"✅ All Slash Commands Synced")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} Security & Automation is Online!')

# ================= WELCOME, LEAVE & AUTO-ROLE EVENTS =================

@bot.event
async def on_member_join(member):
    # 1. Auto-Role Logic
    if server_data["auto_role_id"]:
        role = member.guild.get_role(server_data["auto_role_id"])
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"Failed to add auto-role: {e}")

    # 2. Welcome Logic
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
            leave_date = datetime.datetime.now().strftime("%d-%m-%Y")
            desc = config["description"].replace("{member}", f"**{member.name}**")
            desc += f"\n\n🏟️ **Server:** {member.guild.name}\n📤 **Left On:** {leave_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

# ================= MODALS =================

class WelcomeSetupModal(Modal, title="Customize Welcome"):
    title_in = TextInput(label="Title", default="Welcome!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="Welcome {member}!")
    gif_in = TextInput(label="GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("✅ Welcome Updated!", ephemeral=True)

# ================= COMMANDS =================

@bot.tree.command(name="setup_autorole", description="Set a role to be given automatically when a member joins")
@app_commands.checks.has_permissions(administrator=True)
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    server_data["auto_role_id"] = role.id
    embed = discord.Embed(description=f"✅ **Auto-Role** set to: {role.mention}", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="addword", description="Add a prohibited word to the blocklist")
@app_commands.checks.has_permissions(administrator=True)
async def addword(interaction: discord.Interaction, word: str):
    word = word.lower()
    if word not in server_data["bad_words"]:
        server_data["bad_words"].append(word)
        await interaction.response.send_message(f"✅ `{word}` added to blocklist.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Already in the list.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock the current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    embed = discord.Embed(description="🔒 This channel has been **Locked**.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="unlock", description="Unlock the current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    embed = discord.Embed(description="🔓 This channel has been **Unlocked**.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup_welcome", description="Setup the welcome system")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Customize Welcome", style=discord.ButtonStyle.success)
    async def cb(i): await i.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Welcome Channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Setup the leave system")
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    await interaction.response.send_message(f"📍 Leave Channel set to: {channel.mention}", ephemeral=True)

@bot.tree.command(name="antilink", description="Toggle Anti-Link Security")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    status = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
    await interaction.response.send_message(f"🛡️ Anti-Link Security: **{status}**", ephemeral=True)

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted **{len(deleted)}** messages.")

@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided"):
    try:
        # মেম্বারকে ব্যান করা হচ্ছে
        await member.ban(reason=reason)
        
        # একটি সুন্দর এমবেড তৈরি করা
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"**User:** {member.name}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to ban: {e}", ephemeral=True)
   
@bot.tree.command(name="unban", description="Unban a member using their User ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        # ID থেকে ইউজারকে খুঁজে বের করা
        user = await bot.fetch_user(int(user_id))
        
        # সার্ভার থেকে আনব্যান করা
        await interaction.guild.unban(user)
        
        embed = discord.Embed(
            description=f"✅ Successfully unbanned **{user.name}**.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Could not unban. Check if ID is correct. Error: {e}", ephemeral=True)
    
# ================= SECURITY LOGIC =================

@bot.event
async def on_message(message):
    if message.author.bot: return
    msg_content = message.content.lower()

    # 1. Profanity Filter
    for word in server_data["bad_words"]:
        if word in msg_content:
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Prohibited Language", description=f"{message.author.mention}, watch your language.", color=discord.Color.red())
                await message.channel.send(embed=embed, delete_after=5)
                return 
            except: pass

    # 2. Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        if "http" in msg_content or "discord.gg" in msg_content or ".com" in msg_content:
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Link Blocked", description=f"{message.author.mention}, links are not allowed.", color=discord.Color.orange())
                await message.channel.send(embed=embed, delete_after=5)
                return
            except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
