import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 1. Clear Messages (Purge) ---
    @app_commands.command(name="clear", description="Delete a specific number of messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        if amount < 1:
            return await interaction.followup.send("Please provide a number greater than 0.")
        
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Successfully deleted `{len(deleted)}` messages.")

    # --- 2. Ban Member ---
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot ban this member due to role hierarchy.", ephemeral=True)
        
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"🔨 **{member.name}** has been banned.\n**Reason:** {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to ban: {e}", ephemeral=True)

    # --- 3. Unban Member ---
    @app_commands.command(name="unban", description="Unban a member using their User ID")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ **{user.name}** has been successfully unbanned.")
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found in the ban list.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

    # --- 4. Timeout (Mute) ---
    @app_commands.command(name="timeout", description="Timeout/Mute a member for a specific duration")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot timeout this member.", ephemeral=True)
        
        duration = datetime.timedelta(minutes=minutes)
        try:
            await member.timeout(duration, reason=reason)
            await interaction.response.send_message(f"🔇 **{member.name}** has been timed out for {minutes} minutes.\n**Reason:** {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to timeout: {e}", ephemeral=True)

    # --- 5. Kick Member ---
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot kick this member.", ephemeral=True)
        
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"👞 **{member.name}** has been kicked.\n**Reason:** {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to kick: {e}", ephemeral=True)

    # --- 6. Lock Channel ---
    @app_commands.command(name="lock", description="Lock the current channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"🔒 {channel.mention} has been locked.")

    # --- 7. Unlock Channel ---
    @app_commands.command(name="unlock", description="Unlock a previously locked channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"🔓 {channel.mention} is now unlocked.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
