import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import datetime

# ফাইল পাথ
LEVEL_FILE = 'levels.json'
ECO_FILE = 'economy.json'

def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user) # ৬০ সেকেন্ডে ১ বার XP পাবে

    # --- XP ক্যালকুলেশন (Hard Difficulty) ---
    def get_xp_needed(self, level):
        # ফর্মুলা: 50 * (Level^2) + 100
        # লেভেল ১: ১৫০ XP
        # লেভেল ৫: ১৩৫০ XP
        # লেভেল ১০: ৫১০০ XP
        return 50 * (level ** 2) + 100

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # কুলডাউন চেক (স্প্যাম আটকাতে)
        bucket = self._cd.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after: return # যদি কুলডাউনে থাকে তবে XP পাবে না

        # ডাটা লোড
        data = load_json(LEVEL_FILE)
        uid = str(message.author.id)

        if uid not in data:
            data[uid] = {"xp": 0, "level": 0}

        # XP যোগ করা (১০ থেকে ২০ এর মধ্যে র‍্যান্ডম)
        xp_gain = random.randint(10, 20)
        data[uid]["xp"] += xp_gain
        
        current_xp = data[uid]["xp"]
        current_lvl = data[uid]["level"]
        xp_needed = self.get_xp_needed(current_lvl)

        # --- LEVEL UP CHECK ---
        if current_xp >= xp_needed:
            # লেভেল বাড়ানো
            data[uid]["level"] += 1
            data[uid]["xp"] -= xp_needed # বাকি XP থেকে যাবে
            new_level = data[uid]["level"]
            
            save_json(LEVEL_FILE, data) # লেভেল সেভ করা

            # --- REWARDS CALCULATION ---
            eco_data = load_json(ECO_FILE)
            if uid not in eco_data: eco_data[uid] = {"balance": 0, "lootboxes": 0}

            # ক্যাশ রিওয়ার্ড
            cash_prize = 500
            if new_level == 1:
                cash_prize = 2000 # লেভেল ১ এর জন্য স্পেশাল বোনাস

            # লুটবক্স রিওয়ার্ড
            box_prize = 2 

            # ইকোনমি আপডেট
            eco_data[uid]["balance"] += cash_prize
            eco_data[uid]["lootboxes"] = eco_data.get(uid, {}).get("lootboxes", 0) + box_prize
            save_json(ECO_FILE, eco_data)

            # --- STYLISH LEVEL UP EMBED ---
            embed = discord.Embed(
                title="🎉 LEVEL UP!",
                description=f"Congratulations **{message.author.mention}**!",
                color=discord.Color.from_rgb(255, 215, 0) # গোল্ডেন কালার
            )
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else None)
            
            embed.add_field(name="📈 New Level", value=f"```\nLevel {new_level}\n```", inline=True)
            embed.add_field(name="💰 Cash Earned", value=f"```\n+{cash_prize} Coins\n```", inline=True)
            embed.add_field(name="📦 Lootboxes", value=f"```\n+{box_prize} Boxes\n```", inline=True)
            
            embed.set_footer(text=f"Next Level requires {self.get_xp_needed(new_level)} XP")

            await message.channel.send(embed=embed)
        else:
            save_json(LEVEL_FILE, data)

    # --- RANK COMMAND ---
    @commands.hybrid_command(name="rank", description="📊 Check your current level and XP")
    async def rank(self, ctx, member: discord.Member = None):
        user = member or ctx.author
        uid = str(user.id)
        data = load_json(LEVEL_FILE)

        if uid not in data:
            return await ctx.send("📊 This user hasn't earned any XP yet!")

        lvl = data[uid]["level"]
        xp = data[uid]["xp"]
        needed = self.get_xp_needed(lvl)

        # প্রোগ্রেস বার
        percent = int((xp / needed) * 100)
        bar_length = 10
        filled = int(bar_length * percent / 100)
        bar = "🟦" * filled + "⬜" * (bar_length - filled)

        embed = discord.Embed(
            title=f"📊 Rank Card: {user.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        embed.add_field(name="Level", value=f"**{lvl}**", inline=True)
        embed.add_field(name="XP", value=f"`{xp} / {needed}`", inline=True)
        embed.add_field(name="Progress", value=f"{bar} **{percent}%**", inline=False)
        
        await ctx.send(embed=embed)

    # --- TOP/LEADERBOARD COMMAND ---
    @commands.hybrid_command(name="top", description="🏆 View the global level leaderboard")
    async def top(self, ctx):
        data = load_json(LEVEL_FILE)
        if not data:
            return await ctx.send("📭 No data found!")

        # সর্টিং (লেভেল অনুযায়ী, তারপর XP অনুযায়ী)
        sorted_users = sorted(data.items(), key=lambda x: (x[1]['level'], x[1]['xp']), reverse=True)[:10]

        embed = discord.Embed(title="🏆 Global Level Leaderboard", color=discord.Color.gold())
        desc = ""
        
        for i, (uid, info) in enumerate(sorted_users, 1):
            try:
                user = await self.bot.fetch_user(int(uid))
                name = user.name
            except:
                name = "Unknown User"
            
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"`#{i}`"
            desc += f"{medal} **{name}** — Lv. {info['level']} ({info['xp']} XP)\n"

        embed.description = desc
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
          
