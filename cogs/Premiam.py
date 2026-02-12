import discord
from discord.ext import commands
from discord import app_commands
from utils import PremiumSelectionView, get_theme_color, load_config, PRICES

class PremiumManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. প্রিমিয়াম কেনার কমান্ড ---
    @app_commands.command(name="buy_premium", description="🛒 Upgrade to Premium and unlock Gold Theme")
    async def buy_premium(self, interaction: discord.Interaction):
        color = get_theme_color(interaction.user.id, interaction.guild.id)
        
        # এমবেড (সম্পূর্ণ ইংলিশে)
        embed = discord.Embed(
            title="💎 Premium Store",
            description=(
                "Upgrade now to unlock the **Gold Theme** and exclusive features!\n\n"
                f"👤 **User Premium:** {PRICES['user']}\n"
                "• Works in ALL servers.\n"
                "• Your profile and commands will be **GOLD**.\n\n"
                f"🏰 **Server Premium:** {PRICES['server']}\n"
                "• Works for EVERYONE in this server.\n"
                "• Server embeds will be **GOLD**."
            ),
            color=color
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        await interaction.response.send_message(embed=embed, view=PremiumSelectionView())

    # --- ২. স্ট্যাটাস চেক কমান্ড ---
    @app_commands.command(name="premium_status", description="📊 Check your current subscription status")
    async def premium_status(self, interaction: discord.Interaction):
        config = load_config()
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        color = get_theme_color(interaction.user.id, interaction.guild.id)
        
        # এমবেড টাইটেল ইংলিশে
        embed = discord.Embed(title="📊 Subscription Status", color=color)
        
        # স্ট্যাটাস চেক এবং বাংলা রিপ্লাই সেট করা
        
        # User Status
        if user_id in config.get("premium_users", {}):
            expiry = config["premium_users"][user_id]["expiry"].split("T")[0]
            embed.add_field(name="👤 User Plan", value=f"✅ **সক্রিয় (Premium)**\nমেয়াদ: {expiry}", inline=False)
        else:
            embed.add_field(name="👤 User Plan", value="🟦 **ফ্রি (Basic)**", inline=False)

        # Server Status
        if guild_id in config.get("premium_servers", {}):
            expiry = config["premium_servers"][guild_id]["expiry"].split("T")[0]
            embed.add_field(name="🏰 Server Plan", value=f"✅ **সক্রিয় (Premium)**\nমেয়াদ: {expiry}", inline=False)
        else:
            embed.add_field(name="🏰 Server Plan", value="🟦 **ফ্রি (Basic)**", inline=False)

        # ফুটার মেসেজ (বাংলায় উৎসাহ দেওয়া)
        if color == discord.Color.gold():
            embed.set_footer(text="✨ আপনি একজন প্রিমিয়াম মেম্বার! গোল্ড থিম এনজয় করুন!")
        else:
            embed.set_footer(text="গোল্ড থিম পেতে /buy_premium ব্যবহার করুন!")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumManagement(bot))
