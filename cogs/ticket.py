import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
import asyncio

# --- গ্লোবাল সেটিংস (ড্যাশবোর্ড দিয়ে পরিবর্তন করা যাবে) ---
ticket_config = {
    "title": "📩 Need Support?",
    "description": "Please select a category from the menu below to open a ticket.",
    "gif_url": None
}

# --- ক্যাটাগরি ড্রপডাউন মেনু ---
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BUY", description="Purchase something from us", emoji="🛒"),
            discord.SelectOption(label="REPORT", description="Report an issue or user", emoji="📩"),
            discord.SelectOption(label="CLAIM", description="Claim your rewards or roles", emoji="🎅"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options, custom_id="ticket_select_dropdown")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        user = interaction.user
        
        # পারমিশন সেটআপ
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        # চ্যানেল তৈরি
        channel = await guild.create_text_channel(name=f"{category.lower()}-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"Support - {category}",
            description=f"Hello {user.mention}, welcome to your ticket!\nCategory: **{category}**\nOur staff will help you soon.",
            color=discord.Color.blue()
        )
        if ticket_config["gif_url"]:
            embed.set_image(url=ticket_config["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# --- টিকিটের ভেতরের বাটন (Close) ---
class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_internal")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("This ticket will be deleted in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- মেইন সেটআপ লঞ্চার (ড্রপডাউন সহ) ---
class TicketLaunch(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# --- ড্যাশবোর্ড মোডাল (Customization Form) ---
class TicketDashboardModal(Modal, title="Customize Ticket System"):
    title_in = TextInput(label="Main Title", default=ticket_config["title"])
    desc_in = TextInput(label="Main Description", style=discord.TextStyle.paragraph, default=ticket_config["description"])
    gif_in = TextInput(label="GIF/Image URL", placeholder="https://example.com/image.gif", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_config["title"] = self.title_in.value
        ticket_config["description"] = self.desc_in.value
        ticket_config["gif_url"] = self.gif_in.value if self.gif_in.value else None
        
        await interaction.response.send_message("✅ Dashboard Updated! Use `/setup_ticket` to see the new design.", ephemeral=True)

# --- মূল Cog ক্লাস ---
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_dashboard", description="Customize ticket title, description, and GIF")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket", description="Deploy the dropdown ticket system")
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
