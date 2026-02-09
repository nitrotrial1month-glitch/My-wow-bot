import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import Optional
import datetime

# Railway Token (Ensure this is set in your Railway Environment Variables)
TOKEN = os.getenv('DISCORD_TOKEN')

# সব ডেটা স্টোরেজ একীভূত করা হয়েছে
server_data = {
    "anti_link": {"enabled": False, "blocked": []},
    "bad_words": [], # নিষিদ্ধ শব্দ এখানে জমা হবে
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
        intents.members = True # অবশ্যই অন থাকতে হবে
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Synced all commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 Logged in as {bot.user.name} - Systems Active!')

# ================= WELCOME & LEAVE LOGIC =================

@bot.event
async def on_member_join(member):
    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            join_date = member.joined_at.strftime("%d-%m-%Y")
            guild_name = member.guild.name
            desc = config["description"].replace("{member}", member.mention)
            desc += f"\n\n🏟️ **Server:** {guild_name}\n📅 **Joined At:** {join_date}"
            
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member #{member.guild.member_count}")
            await channel.send(content=f"HEY {member.mention}", embed=embed)

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            join_date = member.joined_at.strftime("%d-%m-%Y") if member.joined_at else "Unknown"
            leave_date = datetime.datetime.now().strftime("%d-%m-%Y")
            guild_name = member.guild.name
            
            desc = config["description"].replace("{member}", f"**{member.name}**")
            desc += f"\n\n🏟️ **Server:** {guild_name}\n📥 **Joined:** {join_date}\n📤 **Left:** {leave_date}"
            
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Goodbye!")
            await channel.send(embed=embed)

# ================= MODALS & DASHBOARDS =================

class WelcomeSetupModal(Modal, title="Customize Welcome Message"):
    title_input = TextInput(label="Title", placeholder="🌸 WELCOME 🌸")
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["welcome"]["description"])
    gif_input = TextInput(label="GIF URL", placeholder="Paste GIF link here.", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"].update({"title": self.title_input.value, "description": self.desc_input.value, "image_url": self.gif_input.value})
        await interaction.response.send_message("✅ Welcome message updated!", ephemeral=True)

class LeaveSetupModal(Modal, title="Customize Leave Message"):
    title_input = TextInput(label="Title", placeholder="💔 GOODBYE 💔")
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["leave"]["description"])
    gif_input = TextInput(label="GIF URL", placeholder="Paste GIF link here.", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        server_data["leave"].update({"title": self.title_input.value, "description": self.desc_input.value, "image_url": self.gif_input.value})
        await interaction.response.send_message("✅ Leave message updated!", ephemeral=True)

# ================= SLASH COMMANDS =================

@bot.tree.command(name="addword", description="নিষিদ্ধ শব্দের তালিকায় শব্দ যোগ করুন")
@app_commands.checks.has_permissions(administrator=True)
async def addword(interaction: discord.Interaction, word: str):
    word_lower = word.lower()
    if word_lower not in server_data["bad_words"]:
        server_data["bad_words"].append(word_lower)
        await interaction.response.send_message(f"✅ `{word}` ব্লকলিস্টে যোগ করা হয়েছে।", ephemeral=True)
    else:
        await interaction.response.send_message("❌ এই শব্দটি আগেই ব্লকলিস্টে আছে।", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Configure welcome system")
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.success)
    async def cb(inter): await inter.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Welcome channel set to: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Configure leave system")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.danger)
    async def cb(inter): await inter.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Leave channel set to: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="antilink", description="Anti-Link Dashboard")
@app_commands.checks.has_permissions(administrator=True)
async def antilink(interaction: discord.Interaction):
    view = View(); btn = Button(label="Toggle Anti-Link", style=discord.ButtonStyle.primary)
    async def cb(inter):
        server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
        status = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
        await inter.response.send_message(f"✅ Anti-Link is now **{status}**", ephemeral=True)
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message("🛡️ Anti-Link Security Dashboard", view=view, ephemeral=True)

@bot.tree.command(name="blocklink", description="নির্দিষ্ট লিংক ব্লক করুন")
@app_commands.checks.has_permissions(administrator=True)
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked"].append(link.lower())
    await interaction.response.send_message(f"✅ `{link}` এখন থেকে ব্লক থাকবে।", ephemeral=True)

@bot.tree.command(name="lock", description="Lock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel has been locked.")

@bot.tree.command(name="unlock", description="Unlock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel has been unlocked.")

@bot.tree.command(name="clear", description="Delete messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Cleared {len(deleted)} messages.")

# ================= MESSAGE FILTERING LOGIC =================

@bot.event
async def on_message(message):
    if message.author.bot: return

    # ১. ব্যাড ওয়ার্ড ফিল্টার
    for word in server_data["bad_words"]:
        if word in message.content.lower():
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, খারাপ শব্দ ব্যবহার করা নিষেধ!", delete_after=5)
                return
            except: pass

    # ২. এন্টি-লিংক ফিল্টার
    if server_data["anti_link"]["enabled"]:
        # যদি মেসেজে কোনো লিংক থাকে
        if "http" in message.content.lower() or ".com" in message.content.lower():
             # নির্দিষ্ট ব্লক করা লিংক চেক করা
             for blocked in server_data["anti_link"]["blocked"]:
                 if blocked in message.content.lower():
                    try:
                        await message.delete()
                        await message.channel.send(f"🚫 {message.author.mention}, এই লিংকটি নিষিদ্ধ!", delete_after=5)
                        return
                    except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - All Systems Active!')

# ================= WELCOME & LEAVE EVENTS =================

@bot.event
async def on_member_join(member):
    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            join_date = member.joined_at.strftime("%d-%m-%Y")
            guild_name = member.guild.name
            desc = config["description"].replace("{member}", member.mention)
            desc += f"\n\n🏟️ **Server:** {guild_name}\n📅 **Joined At:** {join_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member #{member.guild.member_count}")
            await channel.send(content=f"HEY {member.mention}", embed=embed)

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            join_date = member.joined_at.strftime("%d-%m-%Y") if member.joined_at else "Unknown"
            leave_date = datetime.datetime.now().strftime("%d-%m-%Y")
            guild_name = member.guild.name
            desc = config["description"].replace("{member}", f"**{member.name}**")
            desc += f"\n\n🏟️ **Server:** {guild_name}\n📥 **Joined:** {join_date}\n📤 **Left:** {leave_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Goodbye!")
            await channel.send(embed=embed)

# ================= MODALS =================

class WelcomeSetupModal(Modal, title="Customize Welcome Message"):
    title_input = TextInput(label="Title", placeholder="🌸 WELCOME 🌸")
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["welcome"]["description"])
    gif_input = TextInput(label="GIF URL", placeholder="Paste link here.", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"].update({"title": self.title_input.value, "description": self.desc_input.value, "image_url": self.gif_input.value})
        await interaction.response.send_message("✅ Welcome message updated!", ephemeral=True)

class LeaveSetupModal(Modal, title="Customize Leave Message"):
    title_input = TextInput(label="Title", placeholder="💔 GOODBYE 💔")
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["leave"]["description"])
    gif_input = TextInput(label="GIF URL", placeholder="Paste link here.", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["leave"].update({"title": self.title_input.value, "description": self.desc_input.value, "image_url": self.gif_input.value})
        await interaction.response.send_message("✅ Leave message updated!", ephemeral=True)

# ================= SLASH COMMANDS =================

@bot.tree.command(name="addword", description="Add a bad word to blocklist")
async def addword(interaction: discord.Interaction, word: str):
    if not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ No permission!", ephemeral=True)
    word_lower = word.lower()
    if word_lower not in server_data["bad_words"]:
        server_data["bad_words"].append(word_lower)
        await interaction.response.send_message(f"✅ `{word}` added to bad words list.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Word already in list.", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Configure welcome system")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.success)
    async def cb(inter): await inter.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Welcome channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Configure leave system")
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.danger)
    async def cb(inter): await inter.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Leave channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="antilink", description="Anti-Link Dashboard")
async def antilink(interaction: discord.Interaction):
    view = View(); btn = Button(label="Toggle Anti-Link", style=discord.ButtonStyle.primary)
    async def cb(inter):
        server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
        await inter.response.send_message(f"✅ Anti-Link: {'Enabled' if server_data['anti_link']['enabled'] else 'Disabled'}", ephemeral=True)
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message("🛡️ Anti-Link Control", view=view, ephemeral=True)

@bot.tree.command(name="blocklink", description="Block a specific link")
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked"].append(link.lower())
    await interaction.response.send_message(f"✅ `{link}` blocked.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock channel")
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel Locked.")

@bot.tree.command(name="unlock", description="Unlock channel")
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel Unlocked.")

@bot.tree.command(name="clear", description="Clear messages")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Cleared {amount} messages.", ephemeral=True)

# ================= MESSAGE LOGIC =================

@bot.event
async def on_message(message):
    if message.author.bot: return

    # Bad Words Filter
    for word in server_data["bad_words"]:
        if word in message.content.lower():
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, don't use bad words!", delete_after=5)
                return
            except: pass

    # Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        for blocked in server_data["anti_link"]["blocked"]:
            if blocked in message.content.lower():
                try:
                    await message.delete()
                    await message.channel.send(f"🚫 {message.author.mention}, links are not allowed!", delete_after=5)
                    return
                except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
