import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="serverinfo", aliases=["si", "server"], description="Get detailed information about the server")
    async def server_info(self, ctx):
        guild = ctx.guild
        
        # মেম্বার স্ট্যাটাস গণনা
        total_members = guild.member_count
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        
        # চ্যানেল গণনা
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        total_channels = text_channels + voice_channels
        
        # ইমোজি এবং স্টিকার
        emojis = len(guild.emojis)
        stickers = len(guild.stickers)
        
        # বুস্ট ইনফো
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count

        # এমবেড ডিজাইন
        embed = discord.Embed(title=f"🏰 {guild.name} Information", color=0x2b2d31)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        # ১. জেনারেল ইনফো
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 Owner", value=f"{guild.owner.mention}", inline=True)
        embed.add_field(name="📅 Created On", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)

        # ২. মেম্বার ইনফো
        embed.add_field(
            name=f"👥 Members ({total_members})", 
            value=f"👤 Humans: `{human_count}`\n🤖 Bots: `{bot_count}`", 
            inline=True
        )

        # ৩. চ্যানেল ইনফো
        embed.add_field(
            name=f"💬 Channels ({total_channels})", 
            value=f"📝 Text: `{text_channels}`\n🔊 Voice: `{voice_channels}`\n📁 Categories: `{categories}`", 
            inline=True
        )

        # ৪. বুস্ট এবং সিকিউরিটি
        embed.add_field(
            name="💎 Boost Status", 
            value=f"Level: `{boost_level}`\nBoosts: `{boost_count}`", 
            inline=True
        )
        
        # ৫. অন্যান্য স্ট্যাটাস
        verif_level = str(guild.verification_level).title()
        embed.add_field(
            name="🔐 Security", 
            value=f"Verification: `{verif_level}`\nRoles: `{len(guild.roles)}`", 
            inline=True
        )
        embed.add_field(
            name="🎨 Assets", 
            value=f"Emojis: `{emojis}`\nStickers: `{stickers}`", 
            inline=True
        )

        # ফুটারে ইউজারের নাম এবং সময়
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.timestamp = datetime.utcnow()

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
      
