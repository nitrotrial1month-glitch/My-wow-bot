import discord
from discord.ext import commands
import json
import os
import random

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
        # ৬০ সেকেন্ডে ১ বার XP পাবে (Global Cooldown)
        self._cd = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)

    # --- XP ক্যালকুলেশন (Hard Difficulty) ---
    def get_xp_needed(self, level):
        # ফর্মুলা: 50 * (Level^2) + 100
        return 50 * (level ** 2) + 100

    @commands.Cog.listener()
    async def on_message(self, message):
        # বট মেসেজ করলে বা DM হলে কাজ করবে না
        if message.author.bot or message.guild is None: 
            return

        # ১. কুলডাউন চেক
        bucket = self._cd.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after: 
            return # কুলডাউনে থাকলে XP পাবে না, কিন্তু এরর দিবে না (সাইলেন্ট থাকবে)

        # ২. ডাটা লোড
        data = load_json(LEVEL_FILE)
        uid = str(message.author.id)

        if uid not in data:
            data[uid] = {"xp": 0, "level": 0}

        # ৩. XP যোগ করা (১০-২০ এর মধ্যে)
        xp_gain = random.randint(10, 20)
        data[uid]["xp"] += xp_gain
        
        current_xp = data[uid]["xp"]
        current_lvl = data[uid]["level"]
        xp_needed = self.get_xp_needed(current_lvl)

        # ৪. লেভেল আপ চেক
        if current_xp >= xp_needed:
            # লেভেল বাড়ানো
            data[uid]["level"] += 1
            data[uid]["xp"] -= xp_needed # বাকি XP থেকে যাবে (Carry over)
            new_level = data[uid]["level"]
            
            save_json(LEVEL_FILE, data) # লেভেল সেভ

            # --- রিওয়ার্ড দেওয়া ---
            eco_data = load_json(ECO_FILE)
            if uid not in eco_data: 
                eco_data[uid] = {"balance": 0, "lootboxes": 0}

            # ক্যাশ সেট করা
            cash_prize = 500
            if new_level == 1:
                cash_prize = 2000 # লেভেল ১ বোনাস

            # লুটবক্স সেট করা
            box_prize = 2 

            # ইকোনমি আপডেট
            eco_data[uid]["balance"] = eco_data.get(uid, {}).get("balance", 0) + cash_prize
            eco_data[uid]["lootboxes"] = eco_data.get(uid, {}).get("lootboxes", 0) + box_prize
            save_json(ECO_FILE, eco_data)

            # --- লেভেল আপ মেসেজ ---
            embed = discord.Embed(
                title="🎉 LEVEL UP!",
                description=f"Congratulations **{message.author.mention}**!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else None)
            
            embed.add_field(name="📈 New Level", value=f"```\nLevel {new_level}\n```", inline=True)
            embed.add_field(name="💰 Cash Earned", value=f"```\n+{cash_prize} Coins\n```", inline=True)
            embed.add_field(name="📦 Lootboxes", value=f"```\n+{box_prize} Boxes\n```", inline=True)
            
            # পরবর্তী লেভেলের টার্গেট
            next_req = self.get_xp_needed(new_level)
            embed.set_footer(text=f"Next Level requires {next_req} XP")

            try:
                await message.channel.send(embed=embed)
            except:
                pass # পারমিশন না থাকলে মেসেজ দিবে না
        else:
            save_json(LEVEL_FILE, data)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
