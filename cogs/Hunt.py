import discord
from discord.ext import commands
import random
import json
import os

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
        
        # ১. বড় এনিমেল লিস্ট (OwO Style)
        self.animals = {
            "common": ["🐭", "🐹", "🐰", "🐱", "🐶", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐹", "🐣", "🐥", "🐧"],
            "uncommon": ["🐸", "🐵", "🐒", "🐔", "🐤", "🐦", "🦉", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋", "🐌", "🐞"],
            "rare": ["🦄", "🐴", "🐗", "🦒", "🐘", "🦏", "🐫", "🐪", "🦌", "🦓", "🐆", "🐅", "🦍", "🦧", "🐕‍🦺", "🐩"],
            "epic": ["🐍", "🦎", "🦖", "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠", "🐟", "🐬", "🐳", "🐋", "🦈", "🐊"],
            "legendary": ["🐉", "🐲", "🦅", "🐆", "🦈", "🦍", "🦣", "🦦", "🦥", "🦩", "🕊️", "🦜", "🦢", "🦚", "🛸", "👾"]
        }

        # ২. জেমস কনফিগ (৩ টাইপ এবং ৩ ক্যাটাগরি)
        self.gems = {
            # Forest (F) - প্রাণীর সংখ্যা (Count) বাড়াবে
            "F1": {"name": "Forest Gem (Common)", "type": "count", "power": 2, "uses": 5},
            "F2": {"name": "Forest Gem (Uncommon)", "type": "count", "power": 5, "uses": 10},
            "F3": {"name": "Forest Gem (Epic)", "type": "count", "power": 10, "uses": 15},
            
            # Luck (L) - রেয়ার প্রাণী পাওয়ার চান্স বাড়াবে
            "L1": {"name": "Luck Gem (Common)", "type": "luck", "power": 2, "uses": 5},
            "L2": {"name": "Luck Gem (Uncommon)", "type": "luck", "power": 4, "uses": 10},
            "L3": {"name": "Luck Gem (Epic)", "type": "luck", "power": 8, "uses": 15},
            
            # Mythic (M) - সংখ্যা + লাক দুটোই বাড়াবে
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

        if user_id not in data:
            data[user_id] = {"balance": 100, "inventory": {}, "gems": {}, "active_buff": None, "gem_uses": 0}
        
        user_data = data[user_id]
        active_code = user_data.get("active_buff")
        
        multiplier = 1
        luck_boost = 1.0
        durability_msg = ""

        # জেম পাওয়ার প্রোসেসিং (Forest, Luck, Mythic এর কাজ আলাদা করা হয়েছে)
        if active_code in self.gems:
            gem_info = self.gems[active_code]
            if gem_info["type"] == "count":
                multiplier = gem_info["power"]
            elif gem_info["type"] == "luck":
                luck_boost = gem_info["power"]
            elif gem_info["type"] == "mythic":
                multiplier = gem_info["power"] # সংখ্যা বাড়াবে
                luck_boost = gem_info["power"] # লাকও বাড়াবে

            user_data["gem_uses"] -= 1
            if user_data["gem_uses"] <= 0:
                user_data["active_buff"] = None
                durability_msg = f"\n⚠️ Your Gem `{active_code}` has broken!"
            else:
                durability_msg = f"\n🔋 `{active_code}` uses left: {user_data['gem_uses']}"

        # হান্টিং লজিক (লাক বুস্টের প্রভাব)
        chance = random.random() * 100 / luck_boost
        
        if chance <= 1: cat = "legendary"
        elif chance <= 5: cat = "epic"
        elif chance <= 15: cat = "rare"
        elif chance <= 35: cat = "uncommon"
        else: cat = "common"

        animal = random.choice(self.animals[cat])
        total_caught = int(1 * multiplier)

        # ইনভেন্টরি আপডেট
        inventory = user_data.get("inventory", {})
        inventory[animal] = inventory.get(animal, 0) + total_caught
        user_data["inventory"] = inventory
        save_json(data)

        # রেজাল্ট আউটপুট
        await ctx.send(f"🌿 | **{ctx.author.display_name}** caught a **{cat.upper()}** {animal} **x{total_caught}**!{durability_msg}")

    # --- ৪. জেম ব্যবহার কমান্ড ---
    @commands.hybrid_command(name="use")
    async def use_gem(self, ctx, code: str):
        data = load_json()
        user_id = str(ctx.author.id)
        code = code.upper()

        if code not in self.gems:
            return await ctx.send("❌ Invalid Gem Code! (Ex: F1, L2, M3)")

        user_data = data.get(user_id, {})
        if user_data.get("gems", {}).get(code, 0) <= 0:
            return await ctx.send(f"❌ You don't have any `{code}` gems!")

        if user_data.get("active_buff"):
            return await ctx.send(f"⚠️ You already have an active buff: `{user_data['active_buff']}`!")

        # জেম এক্টিভেট করা
        user_data["gems"][code] -= 1
        user_data["active_buff"] = code
        user_data["gem_uses"] = self.gems[code]["uses"]
        save_json(data)

        await ctx.send(f"💎 | **{ctx.author.display_name}**, you used **{self.gems[code]['name']}**! Active for **{user_data['gem_uses']}** hunts.")

    # --- ৫. লুটবক্স ওপেন কমান্ড ---
    @commands.hybrid_command(name="open", aliases=["op", "lb"])
    async def open_box(self, ctx):
        data = load_json()
        user_id = str(ctx.author.id)

        if data.get(user_id, {}).get("lootboxes", 0) <= 0:
            return await ctx.send(f"**{ctx.author.display_name}**, you don't have any boxes! 📦")

        # জেম তৈরির প্রোবাবিলিটি
        tier = random.choices(["1", "2", "3"], weights=[70, 25, 5])[0] # Common, Uncommon, Epic
        g_type = random.choices(["F", "L", "M"], weights=[45, 45, 10])[0] # Forest, Luck, Mythic
        chosen_code = f"{g_type}{tier}"

        # ডাটা আপডেট
        data[user_id]["lootboxes"] -= 1
        if "gems" not in data[user_id]: data[user_id]["gems"] = {}
        data[user_id]["gems"][chosen_code] = data[user_id]["gems"].get(chosen_code, 0) + 1
        save_json(data)

        await ctx.send(f"📦 | **{ctx.author.display_name}**, you found: **{self.gems[chosen_code]['name']}** (`{chosen_code}`)")

async def setup(bot):
    await bot.add_cog(AdvancedHuntingSystem(bot))
            
