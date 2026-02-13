import discord
from discord.ext import commands
from discord import app_commands
import datetime
# Importing logic from utils
from utils import load_config, get_theme_color

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="profile", description="🆔 View user information with a pro look", aliases=["p", "userinfo"])
    @app_commands.describe(user="The user to view")
    async def profile(self, ctx, user: discord.Member = None):
        target = user or ctx.author
        
        # Check server premium status
        color = get_theme_color(ctx.guild.id)
        is_prem = (color == discord.Color.gold())
        
        # Design (Falcon/Nova Style)
        status_text = "✨ Premium Server Member" if is_prem else "🌑 Free Member"
        
        description = (
            f"### 👤 {target.display_name}'s Profile\n"
            f"────────────────────\n"
            f"• **Status:** {status_text}\n"
            f"• **User ID:** `{target.id}`\n"
            f"• **Joined Discord:** <t:{int(target.created_at.timestamp())}:D>\n"
            f"• **Server Join:** <t:{int(target.joined_at.timestamp())}:R>\n"
            f"────────────────────"
        )

        embed = discord.Embed(description=description, color=color)
        
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
            
        # Upselling for Free users
        if not is_prem:
            embed.add_field(
                name="🔒 Locked Features", 
                value="• Animated Badges\n• Custom Dashboards\n• Priority Support\n\n*Use `/buy_premium` to upgrade!*", 
                inline=False
            )
            
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
