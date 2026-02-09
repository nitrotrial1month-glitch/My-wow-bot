import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import asyncio

# কনফিগারেশন স্টোরেজ
ticket_settings = {
    "title": "📩 Need Support?",
    "description": "Click the button below to create a private support ticket!",
    "gif_url": None
}

# ক্লোজ বাটন
class TicketControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("This ticket will close in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# মেইন লঞ্চ বাটন
class TicketLaunch(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket 📩", style=discord.ButtonStyle.success, custom_id="create_ticket_btn")
    async def create(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title="Support System",
            description=f"Hello {user.mention}, how can we help you?",
            color=discord.Color.blue()
        )
        if ticket_settings["gif_url"]:
            embed.set_image(url=ticket_settings["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket: {channel.mention}", ephemeral=True)

# কাস্টমাইজেশন ফরম
class TicketDashboardModal(Modal, title="Ticket Customization"):
    title_input = TextInput(label="Title", default=ticket_settings["title"])
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, default=ticket_settings["description"])
    gif_input = TextInput(label="GIF URL", placeholder="https://example.com/image.gif", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_settings["title"] = self.title_input.value
        ticket_settings["description"] = self.desc_input.value
        ticket_settings["gif_url"] = self.gif_input.value if self.gif_input.value else None
        await interaction.response.send_message("✅ Settings Updated!", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_dashboard", description="Customize ticket settings")
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket", description="Send ticket message")
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=ticket_settings["title"],
            description=ticket_settings["description"],
            color=discord.Color.green()
        )
        if ticket_settings["gif_url"]:
            embed.set_image(url=ticket_settings["gif_url"])
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ Deployed!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
