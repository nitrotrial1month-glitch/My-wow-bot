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

class HuntingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ১. এনিমেল লিস্ট (সব ক্যাটাগরি)
        self.animals = {
            "common": ["🐭", "🐹", "🐰", "🐱", "🐶"],
            "uncommon": ["🐸", "🐷", "🐮", "🦁", "🐵"],
            "rare": ["🦄", "🐴", "🐗", "🦒", "🐘"],
            "epic": ["🐍", "🦎", "🦖", "🦕", "🐙"],
            "legendary": ["🐉", "🐲", "🦅", "🐆", "🦈"]
        }

        # ২. জেমস কনফিগ (৩ টাইপ: Forest, Luck, Mythic)
        self.gems = {
            "F1": {"name": "Forest Gem (Common)", "type": "count", "power": 2, "uses": 5},
            "F2": {"name": "Forest Gem (Uncommon)", "type": "count", "power": 4, "uses": 10},
            "F3": {"name": "Forest Gem (Epic)", "type": "count", "power": 8, "uses": 15},
            
            "L1": {"name": "Luck Gem (Common)", "type": "luck", "power": 2, "uses": 5},
            "L2": {"name": "Luck Gem (Uncommon)", "type": "luck", "power": 4, "uses": 10},
            "L3": {"name": "Luck Gem (Epic)", "type": "luck", "power": 8, "uses": 15},
            
            "M1": {"name": "Mythic Gem (Common)", "type": "mythic", "power": 1.5, "uses": 5},
            "M2": {"name": "Mythic Gem (Uncommon)", "type": "mythic", "power": 2.5, "uses": 10},
            "M3": {"name": "Mythic Gem (Epic)", "type": "mythic", "power": 5, "uses": 15},
        }

    # --- ৩. মেইন হান্ট কমান্ড ---
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

        # জেম পাওয়ার প্রোসেসিং
        if active_code in self.gems:
            gem_info = self.gems[active_code]
            if gem_info["type"] == "count":
                multiplier = gem_info["power"]
            elif gem_info["type"] == "luck":
                luck_boost = gem_info["power"]
            elif gem_info["type"] == "mythic":
                multiplier = gem_info["power"]
                luck_boost = gem_info["power"]

            user_data["gem_uses"] -= 1
            if user_data["gem_uses"] <= 0:
                user_data["active_buff"] = None
                durability_msg = f"\n⚠️ Your Gem `{active_code}` has broken!"
            else:
                durability_msg = f"\n🔋 `{active_code}` uses left: {user_data['gem_uses']}"

        # হান্টিং লজিক (লাক বুস্ট সহ)
        chance = random.random() * 100 / luck_boost
        
        if chance <= 1: cat = "legendary"
        elif chance <= 5: cat = "epic"
        elif chance <= 15: cat = "rare"
        elif chance <= 35: cat = "uncommon"
        else: cat = "common"

        animal = random.choice(self.animals[cat])
        total_caught = int(1 * multiplier)

        # ইনভেন্টরি সেভ
        inventory = user_data.get("inventory", {})
        inventory[animal] = inventory.get(animal, 0) + total_caught
        user_data["inventory"] = inventory
        save_json(data)

        await ctx.send(f"🌿 | **{ctx.author.display_name}** caught a **{cat.upper()}** {animal} **x{total_caught}**!{durability_msg}")

    # --- ৪. জেম ব্যবহার কমান্ড ---
    @commands.hybrid_command(name="use")
    async def use_gem(self, ctx, code: str):
        data = load_json()
        user_id = str(ctx.author.id)
        code = code.upper()

        if code not in self.gems:
            return await ctx.send("❌ Invalid Gem Code!")

        user_data = data.get(user_id, {})
        if user_data.get("gems", {}).get(code, 0) <= 0:
            return await ctx.send(f"❌ You don't have Gem `{code}`!")

        if user_data.get("active_buff"):
            return await ctx.send(f"⚠️ Already using `{user_data['active_buff']}`!")

        user_data["gems"][code] -= 1
        user_data["active_buff"] = code
        user_data["gem_uses"] = self.gems[code]["uses"]
        save_json(data)

        await ctx.send(f"💎 | Activated **{self.gems[code]['name']}** for **{user_data['gem_uses']}** hunts!")

    # --- ৫. লুটবক্স ওপেন কমান্ড ---
    @commands.hybrid_command(name="open", aliases=["op", "lb"])
    async def open_box(self, ctx):
        data = load_json()
        user_id = str(ctx.author.id)

        if data.get(user_id, {}).get("lootboxes", 0) <= 0:
            return await ctx.send(f"**{ctx.author.display_name}**, no boxes! 📦")

        # রেন্ডমলি জেম তৈরি (Tier & Type)
        tier = random.choices(["1", "2", "3"], weights=[70, 25, 5])[0]
        g_type = random.choices(["F", "L", "M"], weights=[45, 45, 10])[0]
        chosen_code = f"{g_type}{tier}"

        data[user_id]["lootboxes"] -= 1
        if "gems" not in data[user_id]: data[user_id]["gems"] = {}
        data[user_id]["gems"][chosen_code] = data[user_id]["gems"].get(chosen_code, 0) + 1
        save_json(data)

        await ctx.send(f"📦 | **{ctx.author.display_name}**, you found: **{self.gems[chosen_code]['name']}** (`{chosen_code}`)")

async def setup(bot):
    await bot.add_cog(HuntingSystem(bot))
