import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# --- Global Database Path ---
DB_FILE = 'economy.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # আপনার কাস্টম Nova কয়েন ইমোজি
        self.emoji_cash = "<:Nova:1453460518764548186>"

    @commands.hybrid_command(name="bal", aliases=["balance", "cash"], description="View your total global earnings!")
    @app_commands.describe(member="The member whose balance you want to see")
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        user_id = str(target.id)
        
        data = load_json(DB_FILE)
        user_data = data.get(user_id, {})
        
        balance = user_data.get("balance", 0)
        streak = user_data.get("streak", 0)

        # --- Premium Styled Embed ---
        embed = discord.Embed(
            title=f"💳 Global Financial Status",
            color=0x5865F2, # Discord Blurple color
            timestamp=discord.utils.utcnow()
        )
        
        # ইউজারের নাম এবং আইকন
        embed.set_author(name=f"{target.name}'s Profile", icon_url=target.display_avatar.url)
        
        # ব্যালেন্স সেকশন (বড় করে দেখানো)
        embed.add_field(
            name="✨ Wallet Balance", 
            value=f"### {self.emoji_cash} **{balance:,}**", 
            inline=False
        )
        
        # স্ট্রিক সেkশন
        embed.add_field(
            name="🔥 Daily Streak", 
            value=f"`{streak} Days`", 
            inline=True
        )

        # ইনভেন্টরি বা মেম্বার স্ট্যাটাস (অতিরিক্ত সৌন্দর্য)
        status = "Wealthy" if balance > 100000 else "Global Citizen"
        embed.add_field(
            name="🏆 Rank Status", 
            value=f"`{status}`", 
            inline=True
        )
        
        # বড় থাম্বনেইল
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # ফুটার উইথ আইকন
        embed.set_footer(
            text=f"Requested by {ctx.author.name} • Global Economy", 
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Balance(bot))
      
