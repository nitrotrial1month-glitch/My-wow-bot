import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio
import datetime

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Complete Data Storage
server_data = {
    "anti_link": {"enabled": False},
    "bad_words": [],
    "auto_role_id": None,
    "afk_users": {},
    "ticket_count": 0,
    "ticket_dashboard": {
        "title": "Support Center",
        "description": "Select a category to open a ticket.",
        "image": "https://i.imgur.com/vHq49Yj.png"
    },
    "ticket_inside": {
        "title": "Support Ticket",
        "description": "Hello {member}, wait for staff.",
        "color": 0x3498db
    },
    "welcome": {"channel_id": None, "title": "Welcome!", "description": "Welcome {member}!", "image": None},
    "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left us."},
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(TicketLauncher())
        self.add_view(TicketControl())
        await self.tree.sync()
        print("✅ All Master Commands & Ticket Views Synced!")

bot = MyBot()

# ================= EVENTS (Welcome, Leave, Auto-Role, AFK, Security) =================

@bot.event
async def on_member_join(member):
    if server_data["auto_role_id"]:
        role = member.guild.get_role(server_data["auto_role_id"])
        if role: await member.add_roles(role)
    
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

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    
    # AFK Logic
    if message.author.id in server_data["afk_users"]:
        del server_data["afk_users"][message.author.id]
        await message.channel.send(f"Welcome back {message.author.mention}!", delete_after=5)

    if message.mentions:
        for m in message.mentions:
            if m.id in server_data["afk_users"]:
                await message.reply(f"📌 {m.name} is AFK: {server_data['afk_users'][m.id]}", delete_after=10)

    # Security (Anti-Link & Bad Words)
    msg = message.content.lower()
    if server_data["anti_link"]["enabled"] and any(x in msg for x in ["http", "discord.gg", ".com"]):
        await message.delete()
        return

    for word in server_data["bad_words"]:
        if word in msg:
            await message.delete()
            return

    await bot.process_commands(message)

# ================= TICKET SYSTEM COMPONENTS =================

class TicketControl(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="c_close")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("Closing...", ephemeral=True)
        await asyncio.sleep(3); await interaction.channel.delete()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, custom_id="c_claim")
    async def claim(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

class TicketLauncher(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.select(placeholder="Open a Ticket", options=[discord.SelectOption(label="Support"), discord.SelectOption(label="Report")], custom_id="t_launch")
    async def callback(self, interaction, select):
        server_data["ticket_count"] += 1
        num = server_data["ticket_count"]
        ch = await interaction.guild.create_text_channel(name=f"ticket-{num}")
        await interaction.response.send_message(f"Ticket: {ch.mention}", ephemeral=True)
        cfg = server_data["ticket_inside"]
        emb = discord.Embed(title=cfg["title"], description=cfg["description"].replace("{member}", interaction.user.mention), color=cfg["color"])
        await ch.send(embed=emb, view=TicketControl())

# ================= DASHBOARD MODALS =================

class DashModal(Modal, title="Edit Ticket Panel"):
    t = TextInput(label="Title", default=server_data["ticket_dashboard"]["title"])
    d = TextInput(label="Desc", style=discord.TextStyle.paragraph, default=server_data["ticket_dashboard"]["description"])
    img = TextInput(label="Image URL", default=server_data["ticket_dashboard"]["image"])
    async def on_submit(self, i):
        server_data["ticket_dashboard"].update({"title":self.t.value,"description":self.d.value,"image":self.img.value})
        await i.response.send_message("✅ Updated!", ephemeral=True)

# ================= ALL SLASH COMMANDS (ENGLISH) =================

@bot.tree.command(name="ban")
async def ban(i, m: discord.Member, r: str = "No reason"): await m.ban(reason=r); await i.response.send_message(f"Banned {m.name}")

@bot.tree.command(name="unban")
async def unban(i, user_id: str): await i.guild.unban(await bot.fetch_user(int(user_id))); await i.response.send_message("Unbanned.")

@bot.tree.command(name="timeout")
async def timeout(i, m: discord.Member, min: int): await m.timeout(datetime.timedelta(minutes=min)); await i.response.send_message(f"Timed out {m.name}")

@bot.tree.command(name="clear")
async def clear(i, amount: int): await i.channel.purge(limit=amount); await i.response.send_message(f"Cleared {amount}", ephemeral=True)

@bot.tree.command(name="lock")
async def lock(i): await i.channel.set_permissions(i.guild.default_role, send_messages=False); await i.response.send_message("Locked.")

@bot.tree.command(name="unlock")
async def unlock(i): await i.channel.set_permissions(i.guild.default_role, send_messages=True); await i.response.send_message("Unlocked.")

@bot.tree.command(name="afk")
async def afk(i, reason: str = "Away"): server_data["afk_users"][i.user.id] = reason; await i.response.send_message("AFK Set.")

@bot.tree.command(name="antilink")
async def antilink(i): server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]; await i.response.send_message(f"Anti-link: {server_data['anti_link']['enabled']}")

@bot.tree.command(name="addword")
async def addword(i, word: str): server_data["bad_words"].append(word.lower()); await i.response.send_message(f"Blocked: {word}")

@bot.tree.command(name="setup_welcome")
async def setup_welcome(i, channel: discord.TextChannel): server_data["welcome"]["channel_id"] = channel.id; await i.response.send_message("Welcome set.")

@bot.tree.command(name="ticket_setup")
async def ticket_setup(i, channel: discord.TextChannel):
    cfg = server_data["ticket_dashboard"]
    emb = discord.Embed(title=cfg["title"], description=cfg["description"])
    if cfg["image"]: emb.set_image(url=cfg["image"])
    await channel.send(embed=emb, view=TicketLauncher()); await i.response.send_message("Panel Deployed.")

@bot.tree.command(name="ticket_dashboard")
async def ticket_dashboard(i):
    v = View(); b = Button(label="Edit Panel", style=discord.ButtonStyle.primary)
    async def cb(interaction): await interaction.response.send_modal(DashModal())
    b.callback = cb; v.add_item(b)
    await i.response.send_message("Dashboard:", view=v, ephemeral=True)

bot.run(TOKEN)
