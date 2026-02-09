import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
import asyncio

# কনফিগারেশন সেটিংস
ticket_config = {
    "title": "📩 Need Support?",
    "description": "Please select a category from the menu below.",
    "gif_url": None
}

# ১. ড্রপডাউন লজিক
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BUY", description="Purchase something", emoji="🛒"),
            discord.SelectOption(label="REPORT", description="Report an issue", emoji="📩"),
            discord.SelectOption(label="CLAIM", description="Claim your rewards", emoji="🎁"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown_menu")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        user = interaction.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"{category.lower()}-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(title=f"Support - {category}", description=f"Hello {user.mention}, welcome to your ticket!\nCategory: **{category}**", color=discord.Color.blue())
        if ticket_config["gif_url"]: embed.set_image(url=ticket_config["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# ২. টিকিটের ভেতরের ক্লোজ বাটন
class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_internal")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("Closing in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# ৩. মেইন লঞ্চার (ড্রপডাউন মেনু দেখানোর জন্য)
class TicketLaunch(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ৪. কাস্টমাইজেশন ড্যাশবোর্ড
class TicketDashboardModal(Modal, title="Customize Ticket System"):
    t_in = TextInput(label="Title", default=ticket_config["title"])
    d_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default=ticket_config["description"])
    g_in = TextInput(label="GIF URL", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_config["title"], ticket_config["description"] = self.t_in.value, self.d_in.value
        ticket_config["gif_url"] = self.g_in.value if self.g_in.value else None
        await interaction.response.send_message("✅ Updated! Now use `/setup_ticket`.", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="ticket_dashboard", description="Customize settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket", description="Send ticket system")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(title=ticket_config["title"], description=ticket_config["description"], color=discord.Color.green())
        if ticket_config["gif_url"]: embed.set_image(url=ticket_config["gif_url"])
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ Deployed!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
    
