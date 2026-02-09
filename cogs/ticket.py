import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import asyncio

# কনফিগারেশন স্টোরেজ
ticket_settings = {
    "title": "📩 Need Support?",
    "description": "Click the button below to create a private support ticket!",
    "gif_url": None
}

# --- টিকিটের ভেতরের কন্ট্রোল (Close & Claim) ---
class TicketControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim 🙋‍♂️", style=discord.ButtonStyle.success, custom_id="claim_ticket")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Only staff can claim tickets!", ephemeral=True)
        await interaction.response.send_message(f"✅ This ticket has been claimed by {interaction.user.mention}")
        self.claim.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Close 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ This ticket will be deleted in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- টিকিট খোলার বাটন ---
class TicketLaunch(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket 📩", style=discord.ButtonStyle.primary, custom_id="launch_ticket")
    async def create(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title="Support System",
            description=f"Hello {user.mention}, our staff will be with you shortly.\nUse the buttons below to Manage.",
            color=discord.Color.blue()
        )
        if ticket_settings["gif_url"]:
            embed.set_image(url=ticket_settings["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# --- কাস্টমাইজেশন ড্যাশবোর্ড ---
class TicketDashboardModal(Modal, title="Ticket Customization"):
    title_in = TextInput(label="Ticket Title", default=ticket_settings["title"])
    desc_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default=ticket_settings["description"])
    gif_in = TextInput(label="GIF URL (Direct Link)", placeholder="https://example.com/image.gif", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_settings["title"] = self.title_in.value
        ticket_settings["description"] = self.desc_in.value
        ticket_settings["gif_url"] = self.gif_in.value if self.gif_in.value else None
        await interaction.response.send_message("✅ Dashboard Settings Updated!", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_dashboard", description="Customize ticket title, text and GIF")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket", description="Send the ticket creation message")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=ticket_settings["title"],
            description=ticket_settings["description"],
            color=0x2ecc71
        )
        if ticket_settings["gif_url"]:
            embed.set_image(url=ticket_settings["gif_url"])
            
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ Ticket System Ready!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
