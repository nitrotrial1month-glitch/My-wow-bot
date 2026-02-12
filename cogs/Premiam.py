import discord
from discord.ext import commands
from discord import app_commands
from utils import PremiumSelectionView, get_theme_color, load_config, PRICES

class PremiumManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- হেল্পার ফাংশন: নাম পরিবর্তন করার জন্য ---
    async def update_bot_identity(self, interaction, is_premium):
        """প্রিমিয়াম হলে নাম পাল্টে '✨ Wow Premium' করবে, না হলে রিসেট করবে"""
        try:
            # বটের নিজের মেম্বার অবজেক্ট
            me = interaction.guild.me
            
            # বট কি নাম পরিবর্তন করতে পারবে? (Permission Check)
            if me.guild_permissions.change_nickname:
                if is_premium:
                    # যদি নাম ইতিমধ্যে পরিবর্তন করা না থাকে তবেই পরিবর্তন করবে
                    if me.nick != "✨ Wow Premium":
                        await me.edit(nick="✨ Wow Premium")
                else:
                    # প্রিমিয়াম না থাকলে নাম রিসেট (None দিলে আসল নাম ফিরে আসে)
                    if me.nick is not None:
                        await me.edit(nick=None)
        except Exception as e:
            print(f"Name change error: {e}") # পারমিশন না থাকলে এরর ইগনোর করবে

    # ====================================================
    # 1. প্রিমিয়াম কেনার কমান্ড
    # ====================================================
    @app_commands.command(name="buy_premium", description="🛒 Upgrade to Premium (Gold Theme & Features)")
    async def buy_premium(self, interaction: discord.Interaction):
        theme_color = get_theme_color(interaction.user.id, interaction.guild.id)
        
        embed = discord.Embed(
            title="💎 Premium Store",
            description=(
                "Choose your plan below to unlock the **Gold Theme**!\n\n"
                f"👤 **User Premium:** {PRICES['user']}\n"
                "• Works in **ALL** servers.\n"
                "• Commands become **GOLD**.\n\n"
                f"🏰 **Server Premium:** {PRICES['server']}\n"
                "• Works for **EVERYONE** in this server.\n"
                "• Bot Name changes to **'✨ Wow Premium'**.\n"
                "• All features become **GOLD**."
            ),
            color=theme_color 
        )
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        embed.set_footer(text="Secure Payment via bKash & Nagad")
        await interaction.response.send_message(embed=embed, view=PremiumSelectionView())

    # ====================================================
    # 2. স্ট্যাটাস চেক এবং নাম পরিবর্তন
    # ====================================================
    @app_commands.command(name="premium_status", description="📊 Check status & Activate Premium Mode")
    async def premium_status(self, interaction: discord.Interaction):
        config = load_config()
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        # ১. কালার লজিক
        theme_color = get_theme_color(interaction.user.id, interaction.guild.id)
        
        # ২. সার্ভার প্রিমিয়াম কিনা চেক করা
        is_server_premium = False
        if guild_id in config.get("premium_servers", {}):
            # এক্সপায়ারি চেক
            # (সহজ করার জন্য এখানে সরাসরি কি চেক করছি, utils.py তে ডেট চেক আছে)
            is_server_premium = True 

        # ৩. বটের নাম আপডেট করা (ম্যাজিক এখানে!) 🪄
        await self.update_bot_identity(interaction, is_server_premium)

        # ৪. এমবেড তৈরি
        embed = discord.Embed(title="📊 Subscription Status", color=theme_color)
        
        # User Status
        if user_id in config.get("premium_users", {}):
            expiry = config["premium_users"][user_id]["expiry"].split("T")[0]
            embed.add_field(name="👤 User Plan", value=f"✅ **PREMIUM**\nExp: {expiry}", inline=False)
        else:
            embed.add_field(name="👤 User Plan", value="🟦 **Free** (Basic Blue)", inline=False)

        # Server Status
        if is_server_premium:
            expiry = config["premium_servers"][guild_id]["expiry"].split("T")[0]
            embed.add_field(name="🏰 Server Plan", value=f"✅ **PREMIUM**\nExp: {expiry}", inline=False)
            embed.add_field(name="✨ Special Effect", value="Bot Name changed to **Wow Premium**!", inline=False)
        else:
            embed.add_field(name="🏰 Server Plan", value="🟦 **Free** (Basic Blue)", inline=False)

        if theme_color == discord.Color.gold():
            embed.set_footer(text="✨ You are a Premium Member! Enjoy the Gold theme!")
        else:
            embed.set_footer(text="Use /buy_premium to unlock Gold Theme & Name!")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumManagement(bot))
