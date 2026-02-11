import discord
from discord.ext import commands
from discord import app_commands
import datetime
from utils import check_advanced_premium

# আপনার দেওয়া অ্যানিমেটেড ব্যাজগুলো
BADGES = {
    "basic": "<a:basic:1471127459326984325>",
    "pro":   "<a:Pro:1471127603682349199>",
    "ultra": "<a:ultra:1471127704148381949>",
    "free":  "🌑"
}

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.hybrid_command ব্যবহার করায় এটি !profile এবং /profile দুটোতেই কাজ করবে
    @commands.hybrid_command(name="profile", description="🆔 Check User Profile (Premium vs Normal)", aliases=["p", "userinfo", "whois"])
    @app_commands.describe(user="The user you want to check")
    async def profile(self, ctx, user: discord.Member = None):
        
        # যদি ইউজার মেনশন না করে, তবে নিজের প্রোফাইল দেখাবে
        target = user or ctx.author
        
        # প্রিমিয়াম চেক করা
        user_data = check_advanced_premium(target.id)
        
        # ====================================================
        # ১. প্রিমিয়াম প্রোফাইল ডিজাইন (VIP Look) 💎
        # ====================================================
        if user_data["active"]:
            tier = user_data["tier"]
            badge = BADGES.get(tier, "💎")
            
            # টিয়ার অনুযায়ী কালার সেট করা
            if tier == "basic": color = discord.Color.orange()
            elif tier == "pro": color = discord.Color.blue()
            elif tier == "ultra": color = discord.Color.gold()
            else: color = discord.Color.green()

            # এমবেড তৈরি
            embed = discord.Embed(
                title=f"{badge} Premium Profile: {target.display_name}", 
                description=f"✨ **Status:** {tier.upper()} Member",
                color=color
            )
            
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)
            
            # প্রিমিয়াম ইনফরমেশন (মেয়াদসহ)
            if "expiry" in user_data:
                expiry_date = user_data["expiry"].strftime('%d %B, %Y')
                remaining = user_data["expiry"] - datetime.datetime.now()
                days_left = remaining.days
                
                embed.add_field(name="🆔 User ID", value=f"`{target.id}`", inline=True)
                embed.add_field(name="⏳ Premium Expires", value=f"**{expiry_date}**\n({days_left} days left)", inline=True)
            
            embed.add_field(name="📅 Joined Discord", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=False)
            
            # ফুটার (ভিআইপি ভাব)
            embed.set_footer(text="🌟 Thank you for being a Premium Member!", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        # ====================================================
        # ২. নরমাল প্রোফাইল ডিজাইন (Free Look) 🌑
        # ====================================================
        else:
            embed = discord.Embed(
                title=f"👤 User Profile: {target.display_name}", 
                description="🌑 **Status:** Free Member",
                color=discord.Color.light_gray() # সাধারণ কালার
            )
            
            if target.avatar:
                embed.set_thumbnail(url=target.avatar.url)
            
            embed.add_field(name="🆔 User ID", value=f"`{target.id}`", inline=True)
            embed.add_field(name="📅 Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
            embed.add_field(name="📅 Joined Discord", value=f"<t:{int(target.created_at.timestamp())}:D>", inline=True)
            
            # আপসেলিং (Upselling) - যাতে তারা প্রিমিয়াম কেনে
            embed.add_field(
                name="🔒 Locked Features", 
                value="• Animated Badges ✨\n• Custom Polls 📊\n• Anti-Link Dashboard 🛡️\n\n👉 Use `/buy_premium` to Upgrade!", 
                inline=False
            )
            
            embed.set_footer(text="Running on Free Tier")

        # মেসেজ পাঠানো (এটি স্ল্যাশ এবং প্রিফিক্স দুটোতেই কাজ করবে)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
          
