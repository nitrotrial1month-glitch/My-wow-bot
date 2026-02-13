import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
# Importing logic from utils
from utils import load_config, get_theme_color

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium(self, guild_id):
        """Checks if the server has Gold Premium status"""
        return get_theme_color(guild_id) == discord.Color.gold()

    @commands.hybrid_command(name="serverinfo", aliases=["si", "server"], description="Get all detailed information about the server")
    async def server_info(self, ctx):
        guild = ctx.guild
        
        # Premium and Theme Logic
        is_prem = self.is_premium(guild.id)
        color = get_theme_color(guild.id)
        
        # Custom Emojis from your request
        p_icon = "<a:ddvs:1471727506385014788>" if is_prem else "<:gd:1471727157641347154>"
        dot = "<a:dot:1433392100451549234>"
        arrow = "<a:emoji_53:1429365638673072300>"

        # Member Statistics
        total_members = guild.member_count
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        
        # Channel Statistics
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        total_channels = text_channels + voice_channels
        
        # Detailed Layout (Falcon/Nova Pro Style)
        description = (
            f"### {p_icon} For testing a Nova\ncommands Information\n\n"
            f"🆔 **Server ID**\n`{guild.id}`\n\n"
            f"👑 **Owner**\n{guild.owner.mention}\n\n"
            f"📅 **Created On**\n{guild.created_at.strftime('%B %d, %Y')}\n\n"
            f"👥 **Members ({total_members})**\n"
            f"{dot} Humans: `{human_count}`\n"
            f"{dot} Bots: `{bot_count}`\n\n"
            f"💬 **Channels ({total_channels})**\n"
            f"📝 Text: `{text_channels}`\n"
            f"🔊 Voice: `{voice_channels}`\n"
            f"📁 Categories: `{categories}`\n\n"
            f"💎 **Boost Status**\n"
            f"Level: `{guild.premium_tier}`\n"
            f"Boosts: `{guild.premium_subscription_count}`\n\n"
            f"🔐 **Security**\n"
            f"Verification: `{str(guild.verification_level).title()}`\n"
            f"Roles: `{len(guild.roles)}`\n\n"
            f"🎨 **Assets**\n"
            f"Emojis: `{len(guild.emojis)}`\n"
            f"Stickers: `{len(guild.stickers)}`"
        )

        embed = discord.Embed(description=description, color=color)
        
        # Setting Images
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        # Footer formatting
        embed.set_footer(text=f"Requested by {ctx.author.name} | Today at {datetime.now().strftime('%I:%M %p')}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
