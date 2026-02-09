import discord
from discord.ext import commands
from discord import app_commands
import asyncio

# টিকিট ক্লোজ করার বাটন
class TicketControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("This ticket will be deleted in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# টিকিট খোলার বাটন
class TicketLaunch(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket 📩", style=discord.ButtonStyle.success, custom_id="create_ticket_btn")
    async def create(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        
        # পারমিশন সেটআপ
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title="Support System",
            description=f"Hello {user.mention}, welcome to your ticket.\nOur team will help you soon!",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# Cog ক্লাস
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_ticket", description="Setup the ticket system in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📩 Need Support?",
            description="Click the button below to create a private support ticket!",
            color=discord.Color.green()
        )
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ Ticket Setup Complete!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))

