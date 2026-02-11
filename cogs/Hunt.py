import discord
from discord.ext import commands
import random
import json
import os
import asyncio

DB_FILE = 'economy.json'

def load_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_json(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class AdvancedHuntingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ১. এনিমেল লিস্ট
        self.animals = {
            "common": ["🐭", "🐹", "🐰", "🐱", "🐶", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐣", "🐥", "🐧"],
            "uncommon": ["🐸", "🐵", "🐒", "🐔", "🐤", "🐦", "🦉", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋", "🐌", "🐞"],
            "rare": ["🦄", "🐗", "🦒", "🐘", "🦏", "🐪", "🦌", "🦓", "🐆", "🐅", "🦍", "🦧", "🐕‍🦺", "🐩"],
            "epic": ["🐍", "🦎", "🦖", "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠", "🐟", "🐬", "🐳", "🐋", "🦈", "🐊"],
            "legendary": ["🐉", "🐲", "🦅", "🐆", "🦈", "🦍", "🦣", "🦦", "🦥", "🦩", "🕊️", "🦜", "🦢", "🦚", "🛸", "👾"]
        }

        # ২. জেমস কনফিগ
        self.gems = {
            "F1": {"name": "Forest Gem (Common)", "type": "count", "power": 2, "uses": 5},
            "F2": {"name": "Forest Gem (Uncommon)", "type": "count", "power": 5, "uses": 10},
            "F3": {"name": "Forest Gem (Epic)", "type": "count", "power": 10, "uses": 15},
            
            "L1": {"name": "Luck Gem (Common)", "type": "luck", "power": 2, "uses": 5},
            "L2": {"name": "Luck Gem (Uncommon)", "type": "luck", "power": 4, "uses": 10},
            "L3": {"name": "Luck Gem (Epic)", "type": "luck", "power": 8, "uses": 15},
            
            "M1": {"name": "Mythic Gem (Common)", "type": "mythic", "power": 1.5, "uses": 5},
            "M2": {"name": "Mythic Gem (Uncommon)", "type": "mythic", "power": 3.0, "uses": 10},
            "M3": {"name": "Mythic Gem (Epic)", "type": "mythic", "power": 6.0, "uses": 15},
        }

    # --- ৩. হান্ট কমান্ড ---
    @commands.hybrid_command(name="hunt", aliases=["h"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def hunt(self, ctx):
        data = load_json()
        user_id = str(ctx.author.id)

        # ডাটা ইনিশিয়ালাইজেশন
        if user_id not in data:
            data[user_id] = {"balance": 100, "inventory": {}, "gems": {}, "active_buff": None, "gem_uses": 0}
        
        user_data = data[user_id]
        
        # ডিফল্ট ভ্যালু সেট করা (যদি জেম না থাকে)
        multiplier = 1
        luck_boost = 1.0
        durability_msg = ""
        
        active_code = user_data.get("active_buff")

        # জেম প্রসেসিং
        if active_code and active_code in self.gems:
            gem_info = self.gems[active_code]
            
            # জেমের টাইপ অনুযায়ী পাওয়ার সেট করা
            if gem_info["type"] == "count":
                multiplier = gem_info["power"]
            elif gem_info["type"] == "luck":
                luck_boost = gem_info["power"]
            elif gem_info["type"] == "mythic":
                multiplier = gem_info["power"]
                luck_boost = gem_info["power"]

            # জেম ব্যবহার কমানো
            user_data["gem_uses"] = user_data.get("gem_uses", 0) - 1
            
            if user_data["gem_uses"] <= 0:
                user_data["active_buff"] = None
                durability_msg = f"\n💔 Your **{gem_info['name']}** has broken!"
            else:
                durability_msg = f"\n💎 **{active_code}** active! Uses left: {user_data['gem_uses']}"

        # হান্টিং লজিক
        # লাক বুস্ট যত বেশি, চান্স ভ্যালু তত কম হবে (মানে ভালো এনিমেল পাওয়ার সম্ভাবনা বাড়বে)
        raw_chance = random.uniform(0, 100)
        final_chance = raw_chance / luck_boost 
        
        cat = "common"
        if final_chance <= 1: cat = "legendary"
        elif final_chance <= 5: cat = "epic"
        elif final_chance <= 15: cat = "rare"
        elif final_chance <= 35: cat = "uncommon"

        # এনিমেল সিলেক্ট করা
        animal_list = self.animals.get(cat, self.animals["common"])
        animal = random.choice(animal_list)
        
        # এনিমেল সংখ্যা (মাল্টিপ্লায়ার সহ)
        count = int(1 * multiplier)

        # ইনভেন্টরি আপডেট
        inventory = user_data.get("inventory", {})
        inventory[animal] = inventory.get(animal, 0) + count
        user_data["inventory"] = inventory
        
        save_json(data)

        # ফাইনাল মেসেজ
        await ctx.send(f"🏹 **{ctx.author.display_name}** went hunting and caught:\n"
                       f"🐾 **{cat.upper()}** {animal} **x{count}**"
                       f"{durability_msg}")

        # Quest আপডেট (যদি থাকে)
        quest_cog = self.bot.get_cog("DailyQuests")
        if quest_cog:
            await quest_cog.update_quest_progress(ctx.author.id, "hunt")

    # --- ৪. কাস্টম কুলডাউন এরর হ্যান্ডলার ---
    @hunt.error
    async def hunt_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            # সময় ফরম্যাট করা (দশমিকের পর ১ ঘর পর্যন্ত)
            time_left = round(error.retry_after, 1)
            embed = discord.Embed(
                description=f"⏳ **{ctx.author.display_name}** Please wait **{time_left}s** before hunting again!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=time_left)
        else:
            raise error # অন্য কোনো এরর হলে কনসোলে দেখাবে

    # --- ৫. জেম ব্যবহার কমান্ড ---
    @commands.hybrid_command(name="use")
    async def use_gem(self, ctx, code: str):
        data = load_json()
        user_id = str(ctx.author.id)
        code = code.upper() # F1, f1 সব কাজ করবে

        if user_id not in data: 
             data[user_id] = {"balance": 0, "inventory": {}, "gems": {}}

        user_data = data[user_id]
        user_gems = user_data.get("gems", {})

        # জেম আছে কিনা চেক
        if code not in self.gems:
            return await ctx.send("❌ Invalid Gem Code! Example: `F1`, `L2`, `M1`")
        
        if user_gems.get(code, 0) <= 0:
            return await ctx.send(f"❌ You don't have any **{code}** gems in your inventory!")

        # অলরেডি বাফ আছে কিনা চেক
        if user_data.get("active_buff"):
            return await ctx.send(f"⚠️ You already have an active gem: **{user_data['active_buff']}**! Wait until it breaks.")

        # জেম অ্যাক্টিভেট করা
        user_gems[code] -= 1
        user_data["active_buff"] = code
        user_data["gem_uses"] = self.gems[code]["uses"]
        
        save_json(data)

        await ctx.send(f"✅ You equipped **{self.gems[code]['name']}**!\n"
                       f"⚡ Effect: **{self.gems[code]['type'].upper()}** Boost\n"
                       f"🔋 Durability: **{user_data['gem_uses']}** hunts")

    # --- ৬. লুটবক্স ওপেন কমান্ড ---
    @commands.hybrid_command(name="open", aliases=["op", "lb"])
    async def open_box(self, ctx):
        data = load_json()
        user_id = str(ctx.author.id)

        user_data = data.get(user_id, {})
        lootboxes = user_data.get("lootboxes", 0)

        if lootboxes <= 0:
            return await ctx.send(f"📦 **{ctx.author.display_name}**, you don't have any lootboxes!")

        # জেম পাওয়ার লজিক
        # টায়ার (Common 70%, Uncommon 25%, Epic 5%)
        tier = random.choices(["1", "2", "3"], weights=[70, 25, 5])[0]
        # টাইপ (Forest 45%, Luck 45%, Mythic 10%)
        g_type = random.choices(["F", "L", "M"], weights=[45, 45, 10])[0]
        
        chosen_code = f"{g_type}{tier}" # যেমন F1 বা M3

        # ডাটা আপডেট
        user_data["lootboxes"] -= 1
        
        if "gems" not in user_data: user_data["gems"] = {}
        user_data["gems"][chosen_code] = user_data["gems"].get(chosen_code, 0) + 1
        
        save_json(data)

        # এমবেড রেজাল্ট
        gem_name = self.gems[chosen_code]['name']
        embed = discord.Embed(
            title="📦 Lootbox Opened!",
            description=f"You found a rare gem!\n💎 **{gem_name}** (`{chosen_code}`)",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedHuntingSystem(bot))
    
