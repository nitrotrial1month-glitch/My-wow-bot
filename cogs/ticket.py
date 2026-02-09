import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
import asyncio

# ক্যাটাগরি অনুযায়ী টিকিটের নাম বা মেসেজ সেট করার জন্য
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BUY", description="Purchase something from us", emoji="🛒"),
            discord.SelectOption(label="REPORT", description="Report an issue or user", emoji="📩"),
            discord.SelectOption(label="CLAIM", description="Claim your rewards or roles", emoji="🎅"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        user = interaction.user
        
        # পারমিশন সেটআপ
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        # চ্যানেল তৈরি (ক্যাটাগরি অনুযায়ী নাম হবে)
        channel = await guild.create_text_channel(name=f"{category.lower()}-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"Support - {category}",
            description=f"Hello {user.mention}, welcome to your ticket!\nCategory: **{category}**\nOur staff will help you soon.",
            color=discord.Color.blue()
        )
        
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket created in {channel.mention}", ephemeral=True)

# টিকিটের কন্ট্রোল বাটন
class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close 🔒", style=discord.ButtonStyle.danger, custom_id="close_btn")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("Deleting in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# মেইন লঞ্চার ভিউ
class TicketLaunch(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_ticket", description="Setup Dropdown Ticket System")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📩 Need Support?",
            description="Please select the appropriate category from the menu below to open a ticket.",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ Ticket System Deployed!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
