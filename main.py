import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# টিকিটের সিরিয়াল নাম্বার সেভ রাখার জন্য (বট রিস্টার্ট দিলে এটি ০ হয়ে যাবে)
# স্থায়ী করতে চাইলে ডাটাবেজ লাগবে। আপাতত এটি ১ থেকে শুরু হবে।
ticket_config = {
    "counter": 0
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # রিস্টার্টের পর বাটন সচল রাখতে ভিউ রেজিস্টার করা
        self.add_view(TicketLauncher())
        await self.tree.sync()
        print(f"✅ Unique Ticket System Synced")

bot = MyBot()

# ================= TICKET UI COMPONENTS =================



class TicketControlView(View):
    """টিকিট চ্যানেলের ভেতরের বাটন (Close & Claim)"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("This ticket will close in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="ticket_claim")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("Only staff can claim tickets!", ephemeral=True)
        
        await interaction.response.send_message(f"✅ This ticket has been claimed by {interaction.user.mention}", ephemeral=False)
        self.claim.disabled = True
        await interaction.message.edit(view=self)

class TicketDropdown(Select):
    """টিকিট ক্যাটাগরি সিলেক্ট করার মেনু"""
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", description="General support queries", emoji="🛠️"),
            discord.SelectOption(label="Reporting", description="Report a member or bug", emoji="🚫"),
            discord.SelectOption(label="Partnership", description="Apply for partnership", emoji="🤝"),
        ]
        super().__init__(placeholder="Why are you opening a ticket?", min_values=1, max_values=1, options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        ticket_config["counter"] += 1
        num = ticket_config["counter"]
        
        guild = interaction.guild
        user = interaction.user
        category_name = "ACTIVE TICKETS"
        
        # ক্যাটাগরি চেক বা তৈরি
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        # চ্যানেল পারমিশন
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # ইউনিক নাম (ticket-1, ticket-2)
        channel = await guild.create_text_channel(
            name=f"ticket-{num}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket for {user.name} | Category: {self.values[0]}"
        )

        await interaction.response.send_message(f"✅ Your ticket is ready: {channel.mention}", ephemeral=True)

        # টিকিটের ভেতরের মেসেজ
        embed = discord.Embed(
            title=f"Ticket #{num} | {self.values[0]}",
            description=f"Hello {user.mention}, thank you for reaching out.\nStaff will be with you shortly. Use the buttons below to manage this ticket.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Ticket Management System")
        await channel.send(embed=embed, view=TicketControlView())

class TicketLauncher(View):
    """মূল বাটন ভিউ"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ================= COMMANDS =================

@bot.tree.command(name="ticket_setup", description="Setup the unique ticket system")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = discord.Embed(
        title="📩 Contact Support",
        description="To create a private ticket with the staff, please select the category from the dropdown menu below.",
        color=discord.Color.from_rgb(47, 49, 54)
    )
    embed.set_image(url="https://i.imgur.com/K4oN1Y6.png") # একটি সুন্দর ব্যানার ইউআরএল দিতে পারেন
    
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message("✅ Ticket System has been setup successfully!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} Ticket Bot is Online!')

bot.run(TOKEN)
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
# --- টিকিট ক্লোজ করার বাটন ভিউ ---
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction):
        await interaction.response.send_message("This ticket will be closed in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- টিকিট ওপেন করার বাটন ভিউ ---
class TicketLauncher(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="📩", custom_id="launcher")
    async def create_ticket(self, interaction: discord.Interaction):
        # টিকিট নম্বর বাড়ানো
        server_data["ticket_count"] += 1
        ticket_number = server_data["ticket_count"]
        
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="TICKETS")
        
        # ক্যাটাগরি না থাকলে তৈরি করবে
        if category is None:
            category = await guild.create_category("TICKETS")

        # পারমিশন সেটআপ: শুধু ইউজার এবং অ্যাডমিন দেখতে পাবে
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # চ্যানেল তৈরি (ticket-1, ticket-2 স্টাইলে)
        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_number}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(f"✅ Ticket created at {channel.mention}", ephemeral=True)

        # টিকিটের ভেতরে ওয়েলকাম মেসেজ
        embed = discord.Embed(
            title="Ticket Support",
            description=f"Hello {interaction.user.mention}, welcome to your support ticket. Please explain your issue and wait for the staff.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=TicketControlView())

# --- টিকিট সেটআপ কমান্ড ---
@bot.tree.command(name="setup_ticket", description="Setup the ticket system in a channel")
@app_commands.checks.has_permissions(administrator=True)
async def setup_ticket(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = discord.Embed(
        title="Support Ticket",
        description="Click the button below to open a new support ticket.",
        color=discord.Color.green()
    )
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message("✅ Ticket system setup complete!", ephemeral=True)
    

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

bot.run(TOKEN)
