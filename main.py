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
    "afk_users": {},  # AFK à¦®à§‡à¦®à§à¦¬à¦¾à¦°à¦¦à§‡à¦° à¦¤à¦¥à§à¦¯ à¦°à¦¾à¦–à¦¾à¦° à¦œà¦¨à§à¦¯
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
            print(f"âœ… All Slash Commands Synced")
        except Exception as e:
            print(f"âŒ Sync Error: {e}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'ðŸš€ {bot.user.name} is Online with All Features!')

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
            desc += f"\n\nðŸŸï¸ **Server:** {member.guild.name}\nðŸ“… **Joined At:** {join_date}"
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
            desc += f"\n\nðŸŸï¸ **Server:** {member.guild.name}\nðŸ“¤ **Left:** {leave_date}"
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            try: await channel.send(embed=embed)
            except: pass

# ================= MODALS (à¦•à¦¾à¦¸à§à¦Ÿà¦®à¦¾à¦‡à¦œà§‡à¦¶à¦¨) =================

class WelcomeSetupModal(Modal, title="Customize Welcome"):
    title_in = TextInput(label="Title", default="Welcome!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="Welcome {member}!")
    gif_in = TextInput(label="GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("âœ… Welcome Updated!", ephemeral=True)

class LeaveSetupModal(Modal, title="Customize Leave"):
    title_in = TextInput(label="Title", default="Goodbye!")
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default="{member} left.")
    gif_in = TextInput(label="GIF URL", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["leave"].update({"title": self.title_in.value, "description": self.desc_in.value, "image_url": self.gif_in.value})
        await interaction.response.send_message("âœ… Leave Updated!", ephemeral=True)

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
                embed = discord.Embed(description=f"ðŸ“Œ **{mentioned.name}** is AFK: {reason}", color=discord.Color.gold())
                try: await message.reply(embed=embed, delete_after=10)
                except: pass

    msg_content = message.content.lower()

    # 3. Profanity/Bad Word Filter
    for word in server_data["bad_words"]:
        if word in msg_content:
            try:
                await message.delete()
                await message.channel.send(f"ðŸš« {message.author.mention}, Watch your language!", delete_after=5)
                return 
            except: pass

    # 4. Anti-Link Filter
    if server_data["anti_link"]["enabled"]:
        is_link = "http" in msg_content or "discord.gg" in msg_content or ".com" in msg_content
        if is_link:
            try:
                await message.delete()
                await message.channel.send(f"ðŸš« {message.author.mention}, Links are not allowed!", delete_after=5)
                return
            except: pass
            
        for blocked in server_data["anti_link"]["blocked_list"]:
            if blocked in msg_content:
                try: await message.delete(); return
                except: pass

    await bot.process_commands(message)

# ================= ALL COMMANDS (à¦†à¦—à§‡à¦° à¦¸à¦¬ + à¦¨à¦¤à§à¦¨ AFK) =================

@bot.tree.command(name="afk", description="Set your status as Away From Keyboard")
async def afk(interaction: discord.Interaction, reason: Optional[str] = "I am currently away!"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"âœ… {interaction.user.mention}, AFK set: **{reason}**")

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message("âŒ My role is not high enough!", ephemeral=True)
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"ðŸ”¨ Banned **{member.name}**")
    except: await interaction.response.send_message("âŒ Permission Error!", ephemeral=True)

@bot.tree.command(name="unban", description="Unban a member via ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"âœ… Unbanned **{user.name}**")
    except: await interaction.response.send_message("âŒ User not found or not banned.", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Setup Welcome System")
@app_commands.checks.has_permissions(administrator=True)
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.success)
    async def cb(i): await i.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"ðŸ“ Welcome Channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Setup Leave System")
@app_commands.checks.has_permissions(administrator=True)
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.danger)
    async def cb(i): await i.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"ðŸ“ Leave Channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_autorole", description="Set Auto-Role")
@app_commands.checks.has_permissions(administrator=True)
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    server_data["auto_role_id"] = role.id
    await interaction.response.send_message(f"âœ… Auto-Role set to: {role.mention}", ephemeral=True)

@bot.tree.command(name="antilink", description="Toggle Anti-Link")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"ðŸ›¡ï¸ Anti-Link: **{'ON' if server_data['anti_link']['enabled'] else 'OFF'}**")

@bot.tree.command(name="blocklink", description="Block specific link pattern")
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked_list"].append(link.lower())
    await interaction.response.send_message(f"âœ… `{link}` added to blocklist.", ephemeral=True)

@bot.tree.command(name="addword", description="Add bad word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"âœ… `{word}` blocked.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("ðŸ”’ Channel Locked.")

@bot.tree.command(name="unlock", description="Unlock channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("ðŸ”“ Channel Unlocked.")

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"ðŸ§¹ Deleted {len(deleted)} messages.")

bot.run(TOKEN)    msg_content = message.content.lower()

    # Security Filters
    for word in server_data["bad_words"]:
        if word in msg_content:
            try: 
                await message.delete()
                return
            except: pass

    if server_data["anti_link"]["enabled"]:
        if any(x in msg_content for x in ["http", "discord.gg", ".com"]):
            try: 
                await message.delete()
                return
            except: pass

    await bot.process_commands(message)

# ================= TICKET SYSTEM COMPONENTS =================

class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close_persistent")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ This ticket will be closed in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="ticket_claim_persistent")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Only staff can claim tickets!", ephemeral=True)
        await interaction.response.send_message(f"✅ This ticket has been claimed by {interaction.user.mention}", ephemeral=False)
        self.claim.disabled = True
        await interaction.message.edit(view=self)

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", description="Help with general issues", emoji="🛠️"),
            discord.SelectOption(label="Report Member", description="Report a member or bug", emoji="🚫")
        ]
        super().__init__(placeholder="Select a category to open a ticket...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown_persistent")

    async def callback(self, interaction: discord.Interaction):
        server_data["ticket_count"] += 1
        num = server_data["ticket_count"]
        
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="TICKETS")
        if not category: category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(name=f"ticket-{num}", category=category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Your ticket is ready: {channel.mention}", ephemeral=True)

        config = server_data["ticket_inside"]
        embed = discord.Embed(
            title=config["title"], 
            description=config["description"].replace("{member}", interaction.user.mention), 
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=TicketControl())

class TicketLauncher(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ================= DASHBOARD MODALS =================

class DashboardEditModal(Modal, title="Edit Ticket Dashboard"):
    title_in = TextInput(label="Main Title", default=server_data["ticket_dashboard"]["title"])
    desc_in = TextInput(label="Main Description", style=discord.TextStyle.paragraph, default=server_data["ticket_dashboard"]["description"])
    img_in = TextInput(label="Image URL", default=server_data["ticket_dashboard"]["image"], required=False)
    async def on_submit(self, interaction: discord.Interaction):
        server_data["ticket_dashboard"].update({"title": self.title_in.value, "description": self.desc_in.value, "image": self.img_in.value})
        await interaction.response.send_message("✅ Main Dashboard updated! Use `/ticket_setup` to refresh.", ephemeral=True)

class InsideEditModal(Modal, title="Edit Inside Message"):
    title_in = TextInput(label="Inside Title", default=server_data["ticket_inside"]["title"])
    desc_in = TextInput(label="Inside Description", style=discord.TextStyle.paragraph, default=server_data["ticket_inside"]["description"])
    async def on_submit(self, interaction: discord.Interaction):
        server_data["ticket_inside"].update({"title": self.title_in.value, "description": self.desc_in.value})
        await interaction.response.send_message("✅ Inside message settings updated!", ephemeral=True)

# ================= MODERATION & ALL SLASH COMMANDS =================

@bot.tree.command(name="lock", description="Lock the current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 This channel has been locked.")

@bot.tree.command(name="unlock", description="Unlock the current channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 This channel has been unlocked.")

@bot.tree.command(name="clear", description="Clear a specific amount of messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Successfully deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="afk", description="Set your AFK status")
async def afk(interaction: discord.Interaction, reason: str = "Away"):
    server_data["afk_users"][interaction.user.id] = reason
    await interaction.response.send_message(f"✅ {interaction.user.mention}, your AFK is set: {reason}")

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if interaction.guild.me.top_role <= member.top_role:
        return await interaction.response.send_message("❌ Cannot ban this user due to role hierarchy.", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member.name} has been banned.")

@bot.tree.command(name="unban", description="Unban a user by ID")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ {user.name} has been unbanned.")

@bot.tree.command(name="ticket_setup", description="Deploy the ticket panel")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    config = server_data["ticket_dashboard"]
    embed = discord.Embed(title=config["title"], description=config["description"], color=discord.Color.green())
    if config["image"]: embed.set_image(url=config["image"])
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message(f"✅ Ticket system setup in {channel.mention}", ephemeral=True)

@bot.tree.command(name="ticket_dashboard", description="Edit ticket panel settings")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_dashboard(interaction: discord.Interaction):
    view = View()
    btn1 = Button(label="Edit Panel", style=discord.ButtonStyle.primary, emoji="📝")
    btn2 = Button(label="Edit Message", style=discord.ButtonStyle.secondary, emoji="💬")
    async def cb1(i): await i.response.send_modal(DashboardEditModal())
    async def cb2(i): await i.response.send_modal(InsideEditModal())
    btn1.callback = cb1; btn2.callback = cb2
    view.add_item(btn1); view.add_item(btn2)
    await interaction.response.send_message("⚙️ **Ticket Control Dashboard**", view=view, ephemeral=True)

@bot.tree.command(name="antilink", description="Toggle Anti-Link filter")
async def antilink(interaction: discord.Interaction):
    server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
    await interaction.response.send_message(f"🛡️ Anti-Link is now {'ON' if server_data['anti_link']['enabled'] else 'OFF'}")

@bot.tree.command(name="addword", description="Block a specific word")
async def addword(interaction: discord.Interaction, word: str):
    server_data["bad_words"].append(word.lower())
    await interaction.response.send_message(f"✅ Word `{word}` has been added to the blacklist.")

@bot.tree.command(name="setup_autorole", description="Set a role to be given automatically to new members")
async def setup_autorole(interaction: discord.Interaction, role: discord.Role):
    server_data["auto_role_id"] = role.id
    await interaction.response.send_message(f"✅ Auto-Role set to: {role.name}")

bot.run(TOKEN)
