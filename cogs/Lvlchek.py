import discord
from discord.ext import commands
import json
import os

# ফাইল পাথ
LEVEL_FILE = 'levels.json'

# JSON লোড করার ফাংশন
def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

class LevelCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # XP ক্যালকুলেশন ফাংশন (প্রোগ্রেস বার দেখানোর জন্য এটি এখানেও লাগবে)
    def get_xp_needed(self, level):
        return 50 * (level ** 2) + 100

    # --- LEVEL CHECK COMMAND ---
    @commands.hybrid_command(name="lvl", description="📊 Check your current global level", aliases=["exp", "level"])
    async def lvl(self, ctx, member: discord.Member = None):
        user = member or ctx.author
        uid = str(user.id)
        data = load_json(LEVEL_FILE)

        # যদি ডাটা না থাকে
        if uid not in data:
            embed = discord.Embed(description=f"🚫 **{user.display_name}** has not earned any XP yet!", color=discord.Color.red())
            return await ctx.send(embed=embed)

        lvl_num = data[uid]["level"]
        xp = data[uid]["xp"]
        
        # পরবর্তী লেভেলের জন্য কত XP লাগবে
        needed = self.get_xp_needed(lvl_num)

        # --- Stylish Progress Bar ---
        percent = min(100, int((xp / needed) * 100))
        bar_length = 12
        filled = int(bar_length * percent / 100)
        
        if filled == bar_length:
            bar = "🟩" * filled 
        else:
            bar = "🟦" * filled + "⬜" * (bar_length - filled)

        # --- Rank Card Embed ---
        embed = discord.Embed(
            title=f"📊 Global Rank Card",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        
        # সুন্দর কোড ব্লক ডিজাইন
        embed.add_field(name="🔰 Level", value=f"```\n{lvl_num}\n```", inline=True)
        embed.add_field(name="✨ XP Earned", value=f"```\n{xp} / {needed}\n```", inline=True)
        
        # প্রোগ্রেস বার
        embed.add_field(name=f"🚀 Progress ({percent}%)", value=f"`{bar}`", inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelCheck(bot))
    
