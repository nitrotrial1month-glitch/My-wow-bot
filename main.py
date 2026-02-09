import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from typing import Optional
import datetime
import asyncio

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Centralized Data Storage
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
        "description": "Hello {member}, our support team will be with you shortly.",
        "color": discord.Color.blue().value
    },
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
        # Registering views to make them persistent after restart
        self.add_view(TicketLauncher())
        self.add_view(TicketControl())
        await self.tree.sync()
        print(f"✅ All Systems, Slash Commands & Ticket Views Synced")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is Online and Ready!')

# ================= EVENTS (WELCOME, LEAVE, AUTO-ROLE) =================

@bot.event
async def on_member_join(member):
    if server_data["auto_role_id"]:
        role = member.guild.get_role(server_data["auto_role_id"])
        if role:
            try: await member.add_roles(role)
            except: pass

    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            desc = config["description"].replace("{member}", member.mention)
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            embed = discord.Embed(title=config["title"], description=config["description"].replace("{member}", member.name), color=config["color"])
            await channel.send(embed=embed)

# ================= AFK & SECURITY LOGIC =================

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # AFK System
    if message.author.id in server_data["afk_users"]:
        del server_data["afk_users"][message.author.id]
        await message.channel.send(f"Welcome back {message.author.mention}, AFK removed!", delete_after=5)

    if message.mentions:
        for mentioned in message.mentions:
            if mentioned.id in server_data["afk_users"]:
                reason = server_data["afk_users"][mentioned.id]
                await message.reply(f"📌 {mentioned.name} is AFK: {reason}", delete_after=10)

    msg_content = message.content.lower()

    # Security Filters
    for word in server_data["bad_words"]:
        if word in msg_content:
            try: await message.delete(); return
            except: pass

    if server_data["anti_link"]["enabled"]:
        if any(x in msg_content for x in ["http", "discord.gg", ".com"]):
            try: await message.delete(); return
            except: pass

    await bot.process_commands(message)

# ================= TICKET SYSTEM COMPONENTS =================

class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="persistent_close")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ Closing in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="persistent_claim")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Staff only!", ephemeral=True)
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}", ephemeral=False)
        self.claim.disabled = True
        await interaction.message.edit(view=self)

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="🛠️"),
            discord.SelectOption(label="Report Member", emoji="🚫")
        ]
        super().__init__(placeholder="Select Category", min_values=1, max_values=1, options=options, custom_id="persistent_drop")

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
        embed = discord.Embed(title=config["title"], description=config["description"].replace("{member}", interaction.user.mention), color=config["color"])
        await channel.send(embed=embed, view=TicketControl())

class TicketLauncher(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ================= DASHBOARD MODALS =================

class DashboardEditModal(Modal, title="Edit Ticket Dashboard"):
    title_in = TextInput(label="Title", default=server_data["ticket_dashboard"]["title"])
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["ticket_dashboard"]["description"])
    img_in = TextInput(label="Image URL", default=server_data["ticket_dashboard"]["image"], required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["ticket_dashboard"].update({"title": self.title_in.value, "description": self.desc_in.value, "image": self.img_in.value})
        await interaction.response.send_message("✅ Dashboard settings updated!", ephemeral=True)

class InsideEditModal(Modal, title="Edit Ticket Inside Message"):
    title_in = TextInput(label="Title", default=server_data["ticket_inside"]["title"])
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["ticket_inside"]["description"])
    async def on_submit(self, interaction: discord.Interaction):
        server_data["ticket_inside"].update({"title": self.title_in.value, "description": self.desc_in.value})
        await interaction.response.send_message("✅ Inside message updated!", ephemeral=True)

# ================= ALL SLASH COMMANDS =================

@bot.tree.command(name="lock", description="Lock current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel Locked.")

@bot.tree.command(name="unlock", description="Unlock current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel Unlocked.")

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {amount} messages.")

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

@bot.tree.command(name="timeout", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
    await member.timeout(datetime.timedelta(minutes=minutes), reason=reason)
    await interaction.response.send_message(f"⏳ Timed out {member.name} for {minutes}m.")

@bot.tree.command(name="ticket_setup", description="Deploy the ticket panel")
async def ticket_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    config = server_data["ticket_dashboard"]
    embed = discord.Embed(title=config["title"], description=config["description"], color=discord.Color.green())
    if config["image"]: embed.set_image(url=config["image"])
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message(f"✅ Ticket system setup in {channel.mention}", ephemeral=True)

@bot.tree.command(name="ticket_dashboard", description="Control ticket settings")
async def ticket_dashboard(interaction: discord.Interaction):
    view = View()
    btn1 = Button(label="Edit Panel", style=discord.ButtonStyle.primary)
    btn2 = Button(label="Edit Message", style=discord.ButtonStyle.secondary)
    async def cb1(i): await i.response.send_modal(DashboardEditModal())
    async def cb2(i): await i.response.send_modal(InsideEditModal())
    btn1.callback = cb1; btn2.callback = cb2
    view.add_item(btn1); view.add_item(btn2)
    await interaction.response.send_message("⚙️ Ticket Control Dashboard", view=view, ephemeral=True)

@bot.tree.command(name="afk", description="Set AFK status")
async def afk(interaction: discord.Interaction, reason: str = "Away"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"✅ AFK set: {reason}")

@bot.tree.command(name="antilink", description="Toggle Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"🛡️ Anti-Link: {'ON' if server_data['anti_link']['enabled'] else 'OFF'}")

@bot.tree.command(name="addword", description="Add word to blacklist")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Word `{word}` added to blacklist.")

@bot.tree.command(name="setup_welcome", description="Set Welcome Channel")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}")

bot.run(TOKEN)
