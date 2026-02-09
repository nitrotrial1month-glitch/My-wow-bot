import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import Optional
import datetime
import random # উইনার সিলেক্ট করার জন্য এটি উপরে ইম্পোর্ট করে নিন

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Centralized Data Storage
server_data = {
    "anti_link": {"enabled": False, "blocked_list": []},
    "bad_words": [],
    "auto_role_id": None,
    "afk_users": {},  # AFK মেম্বারদের তথ্য রাখার জন্য
    "giveaways": {}, # চলমান গিভওয়েগুলোর তথ্য রাখার জন্য
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
            print(f"❌ Sync Error: {e}")
# Persistent views usually need a fixed custom_id
# self.add_view(GiveawayView(None)) 
bot = MyBot()

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} is Online with All Features!')

# ================= WELCOME, LEAVE & AUTO-ROLE EVENTS =================

@bot.event
async def on_member_join(member):
    # 1. Auto-Role
    if server_data["auto_role_id"]:
        role = member.guild.get_role(server_data["auto_role_id"])
        if role:
            try: await member.add_roles(role)
            except: pass

    # 2. Welcome Message
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
            try: await channel.send(content=f"HEY {member.mention}", embed=embed)
            except: pass

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            leave_date = datetime.datetime.now().strftime("%d-%m-%Y")
            desc = config["description"].replace("{member}", f"**{member.name}**")
            desc += f"\n\n🏟️ **Server:** {member.guild.name}\n📤 **Left:** {leave_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            try: await channel.send(embed=embed)
            except: pass

# ================= MODALS (কাস্টমাইজেশন) =================

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

# ================= AFK & SECURITY LOGIC (on_message) =================

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # 1. AFK Removal
    if message.author.id in server_data["afk_users"]:
        del server_data["afk_users"][message.author.id]
        try: await message.channel.send(f"Welcome back {message.author.mention}, AFK removed!", delete_after=5)
        except: pass

    # 2. AFK Mention Notification
    if message.mentions:
        for mentioned in message.mentions:
            if mentioned.id in server_data["afk_users"]:
                reason = server_data["afk_users"][mentioned.id]
                embed = discord.Embed(description=f"📌 **{mentioned.name}** is AFK: {reason}", color=discord.Color.gold())
                try: await message.reply(embed=embed, delete_after=10)
                except: pass

    msg_content = message.content.lower()

    # 3. Profanity/Bad Word Filter
    for word in server_data["bad_words"]:
        if word in msg_content:
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, Watch your language!", delete_after=5)
                return 
            except: pass

    # 4. Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        is_link = "http" in msg_content or "discord.gg" in msg_content or ".com" in msg_content
        if is_link:
            try:
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, Links are not allowed!", delete_after=5)
                return
            except: pass
            
        for blocked in server_data["anti_link"]["blocked_list"]:
            if blocked in msg_content:
                try: await message.delete(); return
                except: pass

    await bot.process_commands(message)

# ================= ALL COMMANDS (আগের সব + নতুন AFK) =================

@bot.tree.command(name="afk", description="Set your status as Away From Keyboard")
async def afk(interaction: discord.Interaction, reason: Optional[str] = "I am currently away!"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"✅ {interaction.user.mention}, AFK set: **{reason}**")

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message("❌ My role is not high enough!", ephemeral=True)
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 Banned **{member.name}**")
    except: await interaction.response.send_message("❌ Permission Error!", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a member via ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ Unbanned **{user.name}**")
    except: await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Setup Welcome System")
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.success)
    async def cb(i): await i.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Welcome Channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Setup Leave System")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.danger)
    async def cb(i): await i.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Leave Channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_autorole", description="Set Auto-Role")
@app_commands.checks.has_permissions(administrator=True)
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    server_data["auto_role_id"] = role.id
    await interaction.response.send_message(f"✅ Auto-Role set to: {role.mention}", ephemeral=True)

@bot.tree.command(name="antilink", description="Toggle Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"🛡️ Anti-Link: **{'ON' if server_data['anti_link']['enabled'] else 'OFF'}**")

@bot.tree.command(name="blocklink", description="Block specific link pattern")
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked_list"].append(link.lower())
    await interaction.response.send_message(f"✅ `{link}` added to blocklist.", ephemeral=True)

@bot.tree.command(name="addword", description="Add bad word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ `{word}` blocked.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel Locked.")

@bot.tree.command(name="unlock", description="Unlock channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel Unlocked.")

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.")

# --- Giveaway Join Button View ---
class GiveawayView(discord.ui.View):
    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.participants = []

    @discord.ui.button(label="Join Giveaway 🎉", style=discord.ButtonStyle.blurple, custom_id="join_giveaway")
    async def join_button(self, interaction: discord.Interaction):
        if interaction.user.id in self.participants:
            return await interaction.response.send_message("❌ You already joined!", ephemeral=True)
        
        self.participants.append(interaction.user.id)
        await interaction.response.send_message("✅ You have successfully joined the giveaway!", ephemeral=True)

# --- Giveaway Start Command ---
@bot.tree.command(name="giveaway_start", description="Start a professional giveaway")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway_start(interaction: discord.Interaction, duration_mins: int, winners: int, prize: str, channel: Optional[discord.TextChannel] = None):
    channel = channel or interaction.channel
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration_mins)
    timestamp = int(end_time.timestamp())

    embed = discord.Embed(
        title="🎉 NEW GIVEAWAY 🎉",
        description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{timestamp}:R>\n**Hosted by:** {interaction.user.mention}",
        color=discord.Color.random()
    )
    embed.set_footer(text="Click the button below to enter!")
    
    await interaction.response.send_message(f"✅ Giveaway started in {channel.mention}", ephemeral=True)
    
    # Sending the giveaway message with Button
    giveaway_msg = await channel.send(embed=embed)
    view = GiveawayView(giveaway_msg.id)
    await giveaway_msg.edit(view=view)

    # Waiting for the duration
    await asyncio.sleep(duration_mins * 60)

    # Picking Winners
    if not view.participants:
        await channel.send(f"☹️ No one joined the giveaway for **{prize}**.")
    else:
        winner_list = random.sample(view.participants, min(len(view.participants), winners))
        winner_mentions = ", ".join([f"<@{w_id}>" for w_id in winner_list])
        
        end_embed = discord.Embed(
            title="🎊 GIVEAWAY ENDED 🎊",
            description=f"**Prize:** {prize}\n**Winners:** {winner_mentions}\n**Participants:** {len(view.participants)}",
            color=discord.Color.gold()
        )
        await giveaway_msg.edit(embed=end_embed, view=None)
        await channel.send(f"Congratulations {winner_mentions}! You won **{prize}**! 🏆")
    
bot.run(TOKEN)
