import os
import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Global Data Storage
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
        "color": 0x3498db
    },
    "welcome": {"channel_id": None, "title": "Welcome!", "description": "Welcome {member}!", "image": None},
    "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} has left us."}
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
        print("✅ All Modules Synced Successfully!")

bot = MyBot()

# --- Automation Events ---
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
    
    # AFK Auto-Remove & Notify
    if message.author.id in server_data["afk_users"]:
        del server_data["afk_users"][message.author.id]
        await message.channel.send(f"Welcome back {message.author.mention}, AFK removed!", delete_after=5)

    if message.mentions:
        for m in message.mentions:
            if m.id in server_data["afk_users"]:
                await message.reply(f"📌 {m.name} is AFK: {server_data['afk_users'][m.id]}", delete_after=10)

    # Security Filter
    msg = message.content.lower()
    if server_data["anti_link"]["enabled"] and any(x in msg for x in ["http", "discord.gg", ".com"]):
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            return

    for word in server_data["bad_words"]:
        if word in msg:
            await message.delete()
            return

    await bot.process_commands(message)
    # --- Moderation Commands ---
@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction, member: discord.Member, reason: str = "No reason"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member.name}")

@bot.tree.command(name="unban", description="Unban a user by ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction, user_id: str):
    await interaction.guild.unban(await bot.fetch_user(int(user_id)))
    await interaction.response.send_message(f"✅ Unbanned user ID: {user_id}")

@bot.tree.command(name="timeout", description="Mute/Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction, member: discord.Member, minutes: int):
    await member.timeout(datetime.timedelta(minutes=minutes))
    await interaction.response.send_message(f"⏳ {member.name} timed out for {minutes}m.")

@bot.tree.command(name="clear", description="Delete messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Cleared {amount} messages.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock current channel")
async def lock(interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel Locked.")

@bot.tree.command(name="unlock", description="Unlock current channel")
async def unlock(interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel Unlocked.")

# --- Security & Utility Commands ---
@bot.tree.command(name="antilink", description="Toggle Anti-Link filter")
async def antilink(interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"🛡️ Anti-Link is now {'ON' if server_data['anti_link']['enabled'] else 'OFF'}")

@bot.tree.command(name="addword", description="Add word to blacklist")
async def addword(interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Word `{word}` blocked.")

@bot.tree.command(name="afk", description="Set AFK status")
async def afk(interaction, reason: str = "Away"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"✅ AFK set: {reason}")

@bot.tree.command(name="setup_welcome", description="Set welcome channel")
async def setup_welcome(interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}")
    from discord.ui import Modal, TextInput

# --- Ticket Components ---
class TicketControl(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="perm_close")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ Deleting in 5s...", ephemeral=False)
        await asyncio.sleep(5); await interaction.channel.delete()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="perm_claim")
    async def claim(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

class TicketLauncher(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.select(placeholder="Select Category", options=[
        discord.SelectOption(label="General Support", emoji="🛠️"),
        discord.SelectOption(label="Report Member", emoji="🚫")
    ], custom_id="perm_select")
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        server_data["ticket_count"] += 1
        num = server_data["ticket_count"]
        ch = await interaction.guild.create_text_channel(name=f"ticket-{num}")
        await interaction.response.send_message(f"✅ Ticket: {ch.mention}", ephemeral=True)
        
        cfg = server_data["ticket_inside"]
        emb = discord.Embed(title=cfg["title"], description=cfg["description"].replace("{member}", interaction.user.mention), color=cfg["color"])
        await ch.send(embed=emb, view=TicketControl())

# --- Dashboard Modal ---
class DashboardModal(Modal, title="Edit Ticket Panel"):
    title_in = TextInput(label="Main Title")
    desc_in = TextInput(label="Main Description", style=discord.TextStyle.paragraph)
    img_in = TextInput(label="Image URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["ticket_dashboard"].update({"title": self.title_in.value, "description": self.desc_in.value, "image": self.img_in.value})
        await interaction.response.send_message("✅ Dashboard Updated!", ephemeral=True)

# --- Ticket Setup Commands ---
@bot.tree.command(name="ticket_setup", description="Deploy Ticket Panel")
async def ticket_setup(interaction, channel: discord.TextChannel):
    cfg = server_data["ticket_dashboard"]
    emb = discord.Embed(title=cfg["title"], description=cfg["description"])
    if cfg["image"]: emb.set_image(url=cfg["image"])
    await channel.send(embed=emb, view=TicketLauncher())
    await interaction.response.send_message("✅ Panel Deployed!", ephemeral=True)

@bot.tree.command(name="ticket_dashboard", description="Control Ticket Settings")
async def ticket_dashboard(interaction: discord.Interaction):
    view = discord.ui.View()
    btn = discord.ui.Button(label="Edit Main Panel", style=discord.ButtonStyle.primary)
    async def btn_cb(i): await i.response.send_modal(DashboardModal())
    btn.callback = btn_cb; view.add_item(btn)
    await interaction.response.send_message("⚙️ Ticket Dashboard:", view=view, ephemeral=True)

# --- Start Bot ---
bot.run(TOKEN)
    
