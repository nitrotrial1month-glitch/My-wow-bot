import discord
from discord.ext import commands
from discord import app_commands
import typing

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 1. Clear Messages (Hybrid) ---
    @commands.hybrid_command(name="clear", description="Delete a specific number of messages")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete")
    async def clear(self, ctx, amount: int):
        if amount < 1:
            return await ctx.send("Please specify a number greater than 0.", ephemeral=True)
        
        # Purge messages
        deleted = await ctx.channel.purge(limit=amount + (1 if ctx.interaction is None else 0))
        
        # Send confirmation (deletes itself after 5 seconds)
        await ctx.send(f"✅ Successfully cleared `{len(deleted)}` messages.", delete_after=5)

    # --- 2. Ban Member (Hybrid) ---
    @commands.hybrid_command(name="ban", description="Ban a member from the server")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("❌ You cannot ban this member due to role hierarchy.", ephemeral=True)
        
        try:
            await member.ban(reason=reason)
            await ctx.send(f"🔨 **{member.name}** has been banned.\n**Reason:** {reason}")
        except Exception as e:
            await ctx.send(f"❌ Failed to ban: {e}", ephemeral=True)

    # --- 3. Unban Member (Hybrid) ---
    @commands.hybrid_command(name="unban", description="Unban a user via ID")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id="The Discord ID of the user")
    async def unban(self, ctx, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user)
            await ctx.send(f"✅ User **{user.name}** has been successfully unbanned.")
        except discord.NotFound:
            await ctx.send("❌ User ID not found in the ban list.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}", ephemeral=True)

    # --- 4. Lock Channel (Hybrid) ---
    @commands.hybrid_command(name="lock", description="Lock the current or a specific channel")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="The channel to lock")
    async def lock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.send_messages == False:
            return await ctx.send(f"❌ {channel.mention} is already locked.", ephemeral=True)
            
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔒 {channel.mention} is now locked for everyone.")

    # --- 5. Unlock Channel (Hybrid) ---
    @commands.hybrid_command(name="unlock", description="Unlock a channel")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="The channel to unlock")
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.send_messages == True or overwrite.send_messages is None:
            return await ctx.send(f"❌ {channel.mention} is not locked.", ephemeral=True)
            
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"🔓 {channel.mention} has been unlocked.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
