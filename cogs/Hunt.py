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

class HuntSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cash_emoji = "<:Nova:1453460518764548186>"
        
        # Comprehensive Animal List
        self.animals = {
            "common": ["🐭", "🐹", "🐰", "🐱", "🐶", "🦊", "🐻", "🐼", "🐨", "🐯"],
            "uncommon": ["🐸", "🐷", "🐮", "🦁", "🐵", "🐒", "🐔", "🐧", "🐦", "🐤"],
            "rare": ["🦄", "🐴", "🐗", "🦒", "🦓", "🐘", "🦏", "🐫", "🐪", "🦌"],
            "epic": ["🐍", "🦎", "🦖", "🦕", "🐢", "🐊", "🐙", "🦑", "🐬", "🐳"],
            "legendary": ["🐉", "🐲", "🦁", "🦅", "🐆", "🦈", "🦍", "🦣", "🦦", "🦥"]
        }

    @commands.hybrid_command(name="hunt", aliases=["h", "H", "Hunt"], description="Spend 10 cash to catch an animal!")
    async def hunt(self, ctx):
        user_id = str(ctx.author.id)
        data = load_json()

        if user_id not in data:
            data[user_id] = {"balance": 0, "inventory": {}, "gems": {"common": 0, "epic": 0, "legendary": 0}, "active_buff": None}
        
        user_data = data[user_id]
        
        if user_data.get("balance", 0) < 10:
            return await ctx.send(f"❌ You don't have enough balance! Hunting costs 10 {self.cash_emoji}", ephemeral=True)

        # Deduct Balance
        user_data["balance"] -= 10
        await ctx.defer()
        
        # Initial Message
        msg = await ctx.send("🏹 **Searching the wilderness...**")
        await asyncio.sleep(1.2)

        # Probability Logic
        rand = random.random()
        if rand < 0.55: category = "common"
        elif rand < 0.80: category = "uncommon"
        elif rand < 0.92: category = "rare"
        elif rand < 0.98: category = "epic"
        else: category = "legendary"

        animal = random.choice(self.animals[category])
        
        # Buff Calculation
        count = 1
        active_buff = user_data.get("active_buff")
        if active_buff == "legendary": count = 10
        elif active_buff == "epic": count = 5
        elif active_buff == "common": count = 2
        
        user_data["active_buff"] = None # Reset buff

        # Update Inventory
        inventory = user_data.get("inventory", {})
        inventory[animal] = inventory.get(animal, 0) + count
        user_data["inventory"] = inventory
        save_json(data)

        # --- OwO Style Embed Design ---
        # স্ক্রিনশটের মতো করে টেক্সট সাজানো হয়েছে
        embed = discord.Embed(color=0x2b2d31) # Dark theme for premium look
        
        header = f"🌿 | **{ctx.author.display_name}** spent 10 {self.cash_emoji} and"
        main_text = f"caught a **{category}** {animal} **x{count}**!"
        
        embed.description = f"{header}\n{main_text}"
        
        if active_buff:
            embed.set_footer(text=f"💎 Buff Active: {active_buff.capitalize()} Gem applied!")
        else:
            embed.set_footer(text=f"New Balance: {user_data['balance']:,}")

        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(name="usegem", description="Activate a gem for multipliers!")
    async def use_gem(self, ctx, gem_type: str):
        user_id = str(ctx.author.id)
        data = load_json()
        
        gem_type = gem_type.lower()
        if gem_type not in ["common", "epic", "legendary"]:
            return await ctx.send("❌ Invalid type! Use: `common`, `epic`, or `legendary`", ephemeral=True)
        
        user_data = data.get(user_id)
        if not user_data or user_data.get("gems", {}).get(gem_type, 0) <= 0:
            return await ctx.send(f"❌ You don't have any `{gem_type}` gems!", ephemeral=True)

        if user_data.get("active_buff"):
            return await ctx.send(f"⚠️ You already have an active buff!", ephemeral=True)

        user_data["gems"][gem_type] -= 1
        user_data["active_buff"] = gem_type
        save_json(data)

        await ctx.send(f"💎 **{gem_type.capitalize()} Gem** activated! Your next hunt will yield more animals.")

async def setup(bot):
    await bot.add_cog(HuntSystem(bot))
