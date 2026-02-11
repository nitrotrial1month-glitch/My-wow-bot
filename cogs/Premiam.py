import discord
from discord.ext import commands
from discord import app_commands
import datetime

# utils.py থেকে শুধুমাত্র ভিউ এবং চেকার ইমপোর্ট করা হচ্ছে
from utils import (
    PremiumTypeView, 
    check_advanced_premium
)

class PremiumManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====================================================
    # 1. প্রিমিয়াম কেনার কমান্ড (Slash Command)
    # ====================================================
    @app_commands.command(name="buy_premium", description="🛒 Buy Premium for Yourself or this Server")
    async def buy_premium(self, interaction: discord.Interaction):
        # একটি সুন্দর এমবেড তৈরি
        embed = discord.Embed(
            title="💎 Premium Store",
            description=(
                "Choose an option below to upgrade:\n\n"
                "👤 **User Premium:**\n"
                "• Works in **ALL** servers where the bot is present.\n"
                "• Access to exclusive user commands.\n\n"
                "🏰 **Server Premium:**\n"
                "• Works for **EVERYONE** in this server.\n"
                "• Unlock limits and advanced features for the server."
            ),
            color=discord.Color.gold()
        )
        # বটের লোগো থাকলে সেটা দেখাবে
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        embed.set_footer(text="Secure Payment via bKash & Nagad")

        # utils.py এর ভিউ কল করা হচ্ছে (এখান থেকেই প্রসেস শুরু হবে)
        await interaction.response.send_message(embed=embed, view=PremiumTypeView())

    # ====================================================
    # 2. স্ট্যাটাস চেক কমান্ড (User & Server)
    # ====================================================
    @app_commands.command(name="premium_status", description="📊 Check your Premium Status & Expiry")
    async def premium_status(self, interaction: discord.Interaction):
        # ইউজার এবং সার্ভার উভয়ের স্ট্যাটাস চেক করা (utils.py এর ফাংশন দিয়ে)
        user_status = check_advanced_premium(interaction.user.id)
        server_status = check_advanced_premium(None, interaction.guild.id)
        
        embed = discord.Embed(title="📊 Premium Status Profile", color=discord.Color.blurple())
        
        # --- User Status Section ---
        if user_status["active"]:
            tier = user_status["tier"].upper()
            embed.add_field(
                name=f"👤 User: **{tier}**", 
                value="✅ Active across all servers.", 
                inline=False
            )
        else:
            embed.add_field(
                name="👤 User: **Free**", 
                value="❌ No active subscription. Use `/buy_premium`.", 
                inline=False
            )

        # --- Server Status Section ---
        if server_status["active"]:
            tier = server_status["tier"].upper()
            embed.add_field(
                name=f"🏰 Server: **{tier}**", 
                value="✅ This server has premium features enabled.", 
                inline=False
            )
        else:
            embed.add_field(
                name="🏰 Server: **Free**", 
                value="❌ No server subscription.", 
                inline=False
            )

        embed.set_footer(text=f"Requested by {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumManagement(bot))
