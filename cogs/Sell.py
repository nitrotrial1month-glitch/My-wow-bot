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
        self.animals = {
            "Common": ["🐭", "🐹", "🐰", "🐱", "🐶", "🦊", "🐻", "🐼", "🐨", "🐯"],
            "Uncommon": ["🐸", "🐷", "🐮", "🦁", "🐵", "🐒", "🐔", "🐧", "🐦", "🐤"],
            "Rare": ["🦄", "🐴", "🐗", "🦒", "🦓", "🐘", "🦏", "🐫", "🐪", "🦌"],
            "Epic": ["🐍", "🦎", "🦖", "🦕", "🐢", "🐊", "🐙", "🦑", "🐬", "🐳"],
            "Legendary": ["🐉", "🐲", "🦁", "🦅", "🐆", "🦈", "🦍", "🦣", "🦦", "🦥"]
        }

    @commands.hybrid_command(name="hunt", aliases=["h", "H", "Hunt"], description="Go hunting for 10 cash!")
    async def hunt(self, ctx):
        user_id = str(ctx.author.id)
        data = load_json()

        if user_id not in data:
            data[user_id] = {"balance": 0, "inventory": {}, "gems": {"common": 0, "epic": 0, "legendary": 0}, "active_buff": None}
        
        user_data = data[user_id]
        if user_data.get("balance", 0) < 10:
            return await ctx.send(f"❌ You don't have enough balance! Hunting costs 10 {self.cash_emoji}", ephemeral=True)

        user_data["balance"] -= 10
        await ctx.defer()
        
        msg = await ctx.send("🏹 **Searching the wild forest...**")
        await asyncio.sleep(1.5)

        rand = random.random()
        if rand < 0.50: category = "Common"
        elif rand < 0.75: category = "Uncommon"
        elif rand < 0.90: category = "Rare"
        elif rand < 0.98: category = "Epic"
        else: category = "Legendary"

        animal = random.choice(self.animals[category])
        count = 1
        active_buff = user_data.get("active_buff")
        
        if active_buff == "legendary": count = 10
        elif active_buff == "epic": count = 5
        elif active_buff == "common": count = 2
        
        user_data["active_buff"] = None
        inventory = user_data.get("inventory", {})
        inventory[animal] = inventory.get(animal, 0) + count
        user_data["inventory"] = inventory
        save_json(data)

        embed = discord.Embed(title="🐾 Hunting Success!", color=0x2ecc71 if category != "Legendary" else 0xf1c40f)
        embed.add_field(name="Animal Caught", value=f"### {animal} x{count}", inline=True)
        embed.add_field(name="Rarity", value=f"`{category}`", inline=True)
        
        if active_buff:
            embed.set_footer(text=f"💎 Buff Active: {active_buff.capitalize()} Gem gave you {count} catches!")
        else:
            embed.set_footer(text=f"Spent 10 Cash • New Balance: {user_data['balance']:,}")
        
        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(name="usegem", description="Activate a gem for your next hunt!")
    async def use_gem(self, ctx, gem_type: str):
        user_id = str(ctx.author.id)
        data = load_json()
        gem_type = gem_type.lower()
        
        if gem_type not in ["common", "epic", "legendary"]:
            return await ctx.send("❌ Invalid gem type! Use: `common`, `epic`, or `legendary`", ephemeral=True)
        
        user_data = data.get(user_id)
        if not user_data or user_data.get("gems", {}).get(gem_type, 0) <= 0:
            return await ctx.send(f"❌ You don't have any `{gem_type}` gems!", ephemeral=True)

        if user_data.get("active_buff"):
            return await ctx.send(f"⚠️ You already have an active buff!", ephemeral=True)

        user_data["gems"][gem_type] -= 1
        user_data["active_buff"] = gem_type
        save_json(data)
        await ctx.send(f"💎 **{gem_type.capitalize()} Gem** activated! Your next hunt will be multiplied.")

async def setup(bot):
    await bot.add_cog(HuntSystem(bot))
      
