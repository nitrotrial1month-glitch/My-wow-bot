import discord
from discord.ext import commands
from datetime import datetime
from typing import Optional

class Announcement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="announce",
        description="Send a professional announcement to a specific channel"
    )
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """
        Both Prefix & Slash Command: Sends an announcement.
        Usage: !announce #channel <message> OR /announce channel: #channel message: <message>
        """
        # Defer the response for Slash Commands to avoid "Interaction Failed"
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        # Create the English Embed
        embed = discord.Embed(
            title="📢 Official Announcement",
            description=message,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        embed.set_footer(
            text=f"Announced by: {ctx.author.name}", 
            icon_url=ctx.author.display_avatar.url
        )

        try:
            # Sending the announcement
            await channel.send(content="@everyone", embed=embed)
            
            # Response handling
            success_msg = f"✅ Announcement successfully sent to {channel.mention}"
            
            if ctx.interaction:
                await ctx.interaction.followup.send(success_msg)
            else:
                await ctx.send(success_msg, delete_after=5)
                await ctx.message.delete()
            
        except discord.Forbidden:
            error_msg = "❌ I do not have permission to send messages in that channel."
            if ctx.interaction:
                await ctx.interaction.followup.send(error_msg)
            else:
                await ctx.send(error_msg)

    # Error Handling
    @announce.error
    async def announce_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("⛔ You don't have permission to use this command.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ Please mention a valid text channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Announcement(bot))
  
