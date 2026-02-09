import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
import asyncio

# --- Configuration Storage ---
ticket_config = {
    "title": "📩 Need Support?",
    "description": "Please select a category from the menu below to open a private support ticket.",
    "gif_url": None
}

# 1. Internal Ticket Controls (Close & Claim Buttons)
class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim 🙋‍♂️", style=discord.ButtonStyle.success, custom_id="claim_btn_en")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ You don't have permission to claim this ticket!", ephemeral=True)
        
        await interaction.response.send_message(f"✅ This ticket has been claimed by {interaction.user.mention}.")
        button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_btn_en")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ This ticket will be deleted in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# 2. Category Dropdown Menu
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BUY", emoji="🛒", description="Inquire about purchases"),
            discord.SelectOption(label="REPORT", emoji="📩", description="Report an issue or user"),
            discord.SelectOption(label="CLAIM", emoji="🎁", description="Claim rewards or roles"),
        ]
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options, custom_id="dropdown_en")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        user = interaction.user
        
        # Channel Permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        
        # Create Ticket Channel
        channel = await guild.create_text_channel(name=f"{category.lower()}-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"Support - {category}", 
            description=f"Hello {user.mention}, welcome to your ticket!\nOur staff will be with you shortly. Use the buttons below to manage this ticket.", 
            color=discord.Color.blue()
        )
        if ticket_config["gif_url"]: 
            embed.set_image(url=ticket_config["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket created successfully: {channel.mention}", ephemeral=True)

# 3. Main Ticket Launcher
class TicketLaunch(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# 4. Customization Dashboard Modal
class TicketDashboardModal(Modal, title="Ticket System Dashboard"):
    t_input = TextInput(label="Embed Title", default=ticket_config["title"])
    d_input = TextInput(label="Embed Description", style=discord.TextStyle.paragraph, default=ticket_config["description"])
    g_input = TextInput(label="GIF/Image URL", placeholder="https://link-to-your-gif.gif", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_config["title"] = self.t_input.value
        ticket_config["description"] = self.d_input.value
        ticket_config["gif_url"] = self.g_input.value if self.g_input.value else None
        await interaction.response.send_message("✅ Settings updated! Use `/setup_ticket` to deploy the new design.", ephemeral=True)

# 5. Ticket Cog Class
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_dashboard", description="Customize the ticket embed and GIF")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket", description="Send the ticket selection message")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=ticket_config["title"], 
            description=ticket_config["description"], 
            color=discord.Color.green()
        )
        if ticket_config["gif_url"]: 
            embed.set_image(url=ticket_config["gif_url"])
            
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ Ticket System Deployed!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
