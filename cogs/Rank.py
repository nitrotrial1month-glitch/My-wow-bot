import discord
from discord.ext import commands
import json
import os

DB_FILE = 'economy.json'

def load_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cash_emoji = "<:Nova:1453460518764548186>"

    @commands.hybrid_command(name="top", aliases=["rank", "leaderboard"], description="Global currency leaderboard")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def leaderboard(self, ctx, page: int = 1):
        data = load_json()
        if not data:
            return await ctx.send("❌ No data found in the economy!")

        # ১. ব্যালেন্স অনুযায়ী ইউজারদের সর্ট করা (Descending Order)
        # যারা বটের ডাটাবেসে আছে তাদের সবাইকে র‍্যাংক করা হচ্ছে
        sorted_users = sorted(data.items(), key=lambda x: x[1].get('balance', 0), reverse=True)
        
        # ২. কমান্ড ব্যবহারকারীর নিজের র‍্যাংক খুঁজে বের করা
        user_rank = 0
        user_balance = 0
        for i, (uid, info) in enumerate(sorted_users):
            if uid == str(ctx.author.id):
                user_rank = i + 1
                user_balance = info.get('balance', 0)
                break

        # ৩. পেজিনেশন লজিক (প্রতি পেজে ১০ জন করে, মোট ২০০ জন পর্যন্ত)
        total_pages = 20 # ২০০ জন / ১০ জন প্রতি পেজ
        if page < 1 or page > total_pages:
            page = 1
        
        start = (page - 1) * 10
        end = start + 10
        top_slice = sorted_users[start:end]

        # ৪. এমবেড তৈরি করা
        embed = discord.Embed(
            title="🏆 Global Currency Leaderboard",
            color=0x2b2d31
        )

        # ৫. সবার উপরে ইউজারের নিজের র‍্যাংক (OwO স্টাইল)
        user_rank_text = f"#{user_rank if user_rank != 0 else 'N/A'}"
        embed.add_field(
            name="Your Rank",
            value=f"`{user_rank_text}` **{ctx.author.display_name}** — {self.cash_emoji} **{user_balance:,}**",
            inline=False
        )

        # ৬. গ্লোবাল লিস্ট তৈরি (টপ ১০ বা নির্দিষ্ট পেজ)
        lb_description = ""
        for i, (uid, info) in enumerate(top_slice, start=start + 1):
            try:
                # ইউজারকে ক্যাশ বা API থেকে খুঁজে বের করা
                user = self.bot.get_user(int(uid)) or await self.bot.fetch_user(int(uid))
                user_name = user.name
            except:
                user_name = f"Unknown User ({uid})"

            balance = info.get('balance', 0)
            
            # টপ ৩ জনের জন্য স্পেশাল ইমোজি
            rank_icon = f"`#{i}`"
            if i == 1: rank_icon = "🥇"
            elif i == 2: rank_icon = "🥈"
            elif i == 3: rank_icon = "🥉"

            lb_description += f"{rank_icon} **{user_name}** — {self.cash_emoji} {balance:,}\n"

        embed.description = f"**Global Top 200**\n{lb_description}"
        embed.set_footer(text=f"Page {page}/{total_pages} • Use 'Wow top <page>' to see more")

        await ctx.send(embed=embed)

    @leaderboard.error
    async def lb_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = f"{error.retry_after:.2f}"
            await ctx.send(f"**⏱ | {ctx.author.display_name}**! Slow down and try again in **{retry_after}s**", delete_after=5)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
          
