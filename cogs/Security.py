import discord
from discord.ext import commands
from discord import app_commands
import datetime

class SecuritySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Kick Command ---
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot kick this member because they have a higher or equal role!", ephemeral=True)
        
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"**Target:** {member.mention}\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to kick member. Error: {e}", ephemeral=True)

    # --- Timeout (Mute) Command ---
    @app_commands.command(name="timeout", description="Timeout a member for a specific duration")
    @app_commands.describe(
        member="The member to timeout", 
        minutes="Duration in minutes", 
        reason="Reason for timeout"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot timeout this member!", ephemeral=True)
        
        duration = datetime.timedelta(minutes=minutes)
        try:
            await member.timeout(duration, reason=reason)
            embed = discord.Embed(
                title="⏳ Member Timed Out",
                description=f"**Target:** {member.mention}\n**Duration:** {minutes} minutes\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to timeout member. Error: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SecuritySystem(bot))
  
