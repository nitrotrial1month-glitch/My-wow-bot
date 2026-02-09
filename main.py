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
    "auto_role_id": None,
    "afk_users": {},  
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
        try:
            await self.tree.sync()
            print(f"✅ All Slash Commands Synced")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is Online and Ready!')

# ================= EVENTS (WELCOME, LEAVE, AUTO-ROLE) =================

@bot.event
async def on_member_join(member):
    # Auto-Role Logic
    if server_data["auto_role_id"]:
        role = member.guild.get_role(server_data["auto_role_id"])
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    # Welcome Message Logic
    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            desc = config["description"].replace("{member}", member.mention)
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]:
                embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await channel.send(embed=embed)
            except:
                pass

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            desc = config["description"].replace("{member}", member.name)
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            try:
                await channel.send(embed=embed)
            except:
                pass

# ================= AFK & SECURITY LOGIC =================

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # 1. AFK Removal
    if message.author.id in server_data["afk_users"]:
        del server_data["afk_users"][message.author.id]
        try:
            await message.channel.send(f"Welcome back {message.author.mention}, your AFK status is removed!", delete_after=5)
        except:
            pass

    # 2. AFK Mention Notification
    for mentioned in message.mentions:
        if mentioned.id in server_data["afk_users"]:
            reason = server_data["afk_users"][mentioned.id]
            embed = discord.Embed(description=f"📌 **{mentioned.name}** is currently AFK: {reason}", color=discord.Color.gold())
            try:
                await message.reply(embed=embed, delete_after=10)
            except:
                pass

    msg_content = message.content.lower()

    # 3. Profanity Filter
    for word in server_data["bad_words"]:
        if word in msg_content:
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Prohibited Language", description=f"{message.author.mention}, watch your language.", color=discord.Color.red())
                await message.channel.send(embed=embed, delete_after=5)
                return 
            except:
                pass

    # 4. Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        if any(link in msg_content for link in ["http", "discord.gg", ".com", ".net", ".org"]):
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Link Blocked", description=f"{message.author.mention}, links are restricted.", color=discord.Color.orange())
                await message.channel.send(embed=embed, delete_after=5)
                return
            except:
                pass

    await bot.process_commands(message)

# ================= MODERATION & SETUP COMMANDS =================

@bot.tree.command(name="afk", description="Set your AFK status")
async def afk(interaction: discord.Interaction, reason: Optional[str] = "I am currently away!"):
    server_data["afk_users"][interaction.user.id] = reason
    embed = discord.Embed(description=f"✅ {interaction.user.mention}, AFK set: **{reason}**", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message("❌ My role is not high enough to ban this person!", ephemeral=True)
    
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 Successfully banned **{member.name}**")
    except:
        await interaction.response.send_message("❌ Failed to ban. Check my permissions.", ephemeral=True)

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Cleared **{len(deleted)}** messages.")
    except:
        await interaction.followup.send("❌ Something went wrong while clearing.")

@bot.tree.command(name="antilink", description="Toggle Anti-Link Security")
@app_commands.checks.has_permissions(administrator=True)
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    status = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
    await interaction.response.send_message(f"🛡️ Anti-Link is now **{status}**")

@bot.tree.command(name="addword", description="Add a bad word to blocklist")
@app_commands.checks.has_permissions(administrator=True)
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Word `{word}` has been blocked.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock this channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel has been locked.")

@bot.tree.command(name="unlock", description="Unlock this channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel has been unlocked.")

bot.run(TOKEN)
    if server_data["anti_link"]["enabled"]:
        if "http" in msg_content or "discord.gg" in msg_content or ".com" in msg_content:
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Link Blocked", description=f"{message.author.mention}, links are not allowed.", color=discord.Color.orange())
                await message.channel.send(embed=embed, delete_after=5)
                return
            except: pass

    await bot.process_commands(message)

# ================= MODERATION & SETUP COMMANDS =================

@bot.tree.command(name="afk", description="Set your AFK status")
async def afk(interaction: discord.Interaction, reason: Optional[str] = "I am currently away!"):
    server_data["afk_users"][interaction.user.id] = reason
    embed = discord.Embed(description=f"✅ {interaction.user.mention}, AFK set: **{reason}**", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup_autorole", description="Set a join role")
@app_commands.checks.has_permissions(administrator=True)
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    server_data["auto_role_id"] = role.id
    await interaction.response.send_message(f"✅ Auto-Role: {role.name}", ephemeral=True)

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

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message("❌ Role error!", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member.name}")

@bot.tree.command(name="unban", description="Unban a user")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ Unbanned {user.name}")

@bot.tree.command(name="clear", description="Clear chat")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Cleared {amount} messages.")

@bot.tree.command(name="antilink", description="Toggle Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"🛡️ Anti-Link: {'ON' if server_data['anti_link']['enabled'] else 'OFF'}")

@bot.tree.command(name="addword", description="Block a word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Blocked: `{word}`")

bot.run(TOKEN)
    if server_data["anti_link"]["enabled"]:
        if "http" in msg_content or "discord.gg" in msg_content or ".com" in msg_content:
            try:
                await message.delete()
                embed = discord.Embed(title="🚫 Link Blocked", description=f"{message.author.mention}, links are not allowed.", color=discord.Color.orange())
                await message.channel.send(embed=embed, delete_after=5)
                return
            except: pass

    await bot.process_commands(message)

# ================= MODERATION & SETUP COMMANDS =================

@bot.tree.command(name="afk", description="Set your AFK status")
async def afk(interaction: discord.Interaction, reason: Optional[str] = "I am currently away!"):
    server_data["afk_users"][interaction.user.id] = reason
    embed = discord.Embed(description=f"✅ {interaction.user.mention}, AFK set: **{reason}**", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup_autorole", description="Set a join role")
@app_commands.checks.has_permissions(administrator=True)
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    server_data["auto_role_id"] = role.id
    await interaction.response.send_message(f"✅ Auto-Role: {role.name}", ephemeral=True)

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

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message("❌ Role error!", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member.name}")

@bot.tree.command(name="unban", description="Unban a user")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ Unbanned {user.name}")

@bot.tree.command(name="clear", description="Clear chat")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Cleared {amount} messages.")

@bot.tree.command(name="antilink", description="Toggle Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"🛡️ Anti-Link: {'ON' if server_data['anti_link']['enabled'] else 'OFF'}")

@bot.tree.command(name="addword", description="Block a word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Blocked: `{word}`")

bot.run(TOKEN)

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
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    # Check if the bot's role is high enough
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message(
            "❌ Cannot ban this member! My role must be higher than theirs in the hierarchy.", 
            ephemeral=True
        )
    
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"**User:** {member.name}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I lack the required permissions to perform this action.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a member using their User ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        # Fetching the user object using the ID provided
        user = await bot.fetch_user(int(user_id))
        
        # Attempting to unban the user from the guild
        await interaction.guild.unban(user)
        
        # Creating a unique success embed
        embed = discord.Embed(
            title="🔓 Member Unbanned",
            description=f"Successfully restored access for **{user.name}**.",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User ID", value=user_id, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Security System Updated")

        await interaction.response.send_message(embed=embed)
        
    except ValueError:
        await interaction.response.send_message("❌ Invalid User ID. Please provide a numeric ID.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("❌ This user is not found in the ban list.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I do not have permission to unban members.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
        

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
