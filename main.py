import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import Optional
import datetime

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# একীভূত ডেটা স্টোরেজ
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
        print(f"✅ Synced Slash Commands")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is Online!')

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
            desc = config["description"].replace("{member}", f"**{member.name}**")
            desc += f"\n\n🏟️ **Server:** {member.guild.name}\n📥 **Joined:** {join_date}\n📤 **Left:** {leave_date}"
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

class LeaveSetupModal(Modal, title="Customize Leave"):
    title_in = TextInput(label="Title", default="Goodbye!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="{member} left.")
    gif_in = TextInput(label="GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["leave"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("✅ Leave Updated!", ephemeral=True)

# ================= COMMANDS =================

@bot.tree.command(name="addword", description="নিষিদ্ধ শব্দ যোগ করুন")
@app_commands.checks.has_permissions(administrator=True)
async def addword(interaction: discord.Interaction, word: str):
    word = word.lower()
    if word not in server_data["bad_words"]:
        server_data["bad_words"].append(word)
        await interaction.response.send_message(f"✅ `{word}` ব্লকলিস্টে যোগ হয়েছে।", ephemeral=True)
    else:
        await interaction.response.send_message("❌ এটি আগেই আছে।", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Welcome Setup")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.success)
    async def cb(i): await i.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Leave Setup")
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.danger)
    async def cb(i): await i.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="antilink", description="Toggle Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    status = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
    await interaction.response.send_message(f"🛡️ Anti-Link: **{status}**", ephemeral=True)

@bot.tree.command(name="blocklink", description="নির্দিষ্ট লিংক ব্লক করুন")
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked_list"].append(link.lower())
    await interaction.response.send_message(f"✅ `{link}` ব্লক হয়েছে।", ephemeral=True)

@bot.tree.command(name="clear", description="Clear messages")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.")

# ================= SECURITY LOGIC =================



@bot.event
async def on_message(message):
    if message.author.bot: return

    # ১. ব্যাড ওয়ার্ড ফিল্টার
    msg_content = message.content.lower()
    for word in server_data["bad_words"]:
        if word in msg_content:
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, গালি দেওয়া নিষেধ!", delete_after=5)
                return 
            except: pass

    # ২. এন্টি-লিংক লজিক
    if server_data["anti_link"]["enabled"]:
        # যদি সাধারণ লিংক থাকে অথবা নির্দিষ্ট ব্লক করা লিংক থাকে
        if "http" in msg_content or "discord.gg" in msg_content:
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, লিংক দেওয়া নিষেধ!", delete_after=5)
                return
            except: pass
            
        for blocked in server_data["anti_link"]["blocked_list"]:
            if blocked in msg_content:
                try:
                    await message.delete()
                    await message.channel.send(f"🚫 নিষিদ্ধ লিংক!", delete_after=5)
                    return
                except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
