import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Centralized Ticket Data
server_data = {
    "ticket_count": 0,
    "dashboard": {
        "title": "📩 Support Center",
        "description": "Select a category to open a ticket.",
        "image": "https://i.imgur.com/vHq49Yj.png"
    },
    "inside_message": {
        "title": "Support Ticket",
        "description": "Hello {member}, please wait for staff.",
        "color": discord.Color.blue().value
    }
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Persistent Views - রিস্টার্টের পর বাটন সচল রাখতে
        self.add_view(TicketLauncher())
        self.add_view(TicketControl())
        await self.tree.sync()

bot = MyBot()

# ================= MODALS FOR DASHBOARD =================

class DashboardEditModal(Modal, title="Edit Ticket Dashboard"):
    title_in = TextInput(label="Main Title", default=server_data["dashboard"]["title"])
    desc_in = TextInput(label="Main Description", style=discord.TextStyle.paragraph, default=server_data["dashboard"]["description"])
    img_in = TextInput(label="Image URL", default=server_data["dashboard"]["image"], required=False)

    async def on_submit(self, interaction: discord.Interaction):
        server_data["dashboard"].update({
            "title": self.title_in.value,
            "description": self.desc_in.value,
            "image": self.img_in.value
        })
        await interaction.response.send_message("✅ Dashboard Settings Updated! Use `/ticket_setup` to see changes.", ephemeral=True)

class InsideEditModal(Modal, title="Edit Inside Ticket Message"):
    title_in = TextInput(label="Ticket Title", default=server_data["inside_message"]["title"])
    desc_in = TextInput(label="Ticket Description", style=discord.TextStyle.paragraph, default=server_data["inside_message"]["description"])

    async def on_submit(self, interaction: discord.Interaction):
        server_data["inside_message"].update({
            "title": self.title_in.value,
            "description": self.desc_in.value
        })
        await interaction.response.send_message("✅ Inside Ticket Message Updated!", ephemeral=True)

# ================= TICKET VIEWS =================

class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="persistent_close")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ Closing in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="persistent_claim")
    async def claim(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}", ephemeral=False)
        self.claim.disabled = True
        await interaction.message.edit(view=self)

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", emoji="🛠️"),
            discord.SelectOption(label="Report Member", emoji="🚫")
        ]
        super().__init__(placeholder="Choose category...", custom_id="persistent_drop")

    async def callback(self, interaction: discord.Interaction):
        server_data["ticket_count"] += 1
        num = server_data["ticket_count"]
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await interaction.guild.create_text_channel(name=f"ticket-{num}", overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ticket: {channel.mention}", ephemeral=True)

        # টিকিট চ্যানেলের ভেতরের মেসেজ
        config = server_data["inside_message"]
        embed = discord.Embed(title=config["title"], description=config["description"].replace("{member}", interaction.user.mention), color=config["color"])
        await channel.send(embed=embed, view=TicketControl())

class TicketLauncher(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ================= COMMANDS =================

@bot.tree.command(name="ticket_setup", description="Deploy the ticket system")
async def ticket_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    config = server_data["dashboard"]
    embed = discord.Embed(title=config["title"], description=config["description"], color=discord.Color.blue())
    if config["image"]: embed.set_image(url=config["image"])
    
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message("✅ Ticket System Deployed!", ephemeral=True)

@bot.tree.command(name="ticket_dashboard", description="Control Ticket Settings")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_dashboard(interaction: discord.Interaction):
    view = View()
    btn1 = Button(label="Edit Main Dashboard", style=discord.ButtonStyle.primary)
    btn2 = Button(label="Edit Inside Message", style=discord.ButtonStyle.secondary)
    
    async def cb1(i): await i.response.send_modal(DashboardEditModal())
    async def cb2(i): await i.response.send_modal(InsideEditModal())
    
    btn1.callback = cb1; btn2.callback = cb2
    view.add_item(btn1); view.add_item(btn2)
    
    await interaction.response.send_message("⚙️ **Ticket Control Dashboard**\nChoose what to customize:", view=view, ephemeral=True)

@bot.event
async def on_ready():
    print(f'🚀 Bot is Ready!')

bot.run(TOKEN)
