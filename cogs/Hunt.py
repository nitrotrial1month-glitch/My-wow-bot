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
        
        # এনিমেল লিস্ট (প্রতিটি ১০টি করে)
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
            return await ctx.send(f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! হান্ট করতে ১০ {self.cash_emoji} লাগবে।", ephemeral=True)

        user_data["balance"] -= 10
        await ctx.defer()
        
        msg = await ctx.send("🏹 **বনের মধ্যে শিকার খুঁজছি...**")
        await asyncio.sleep(1.5)

        # প্রোবাবিলিটি লজিক
        rand = random.random()
        if rand < 0.50: category = "Common"
        elif rand < 0.75: category = "Uncommon"
        elif rand < 0.90: category = "Rare"
        elif rand < 0.98: category = "Epic"
        else: category = "Legendary"

        animal = random.choice(self.animals[category])
        
        # জেম বা বাফ চেক (অটোমেটিক নয়, আগে থেকে এক্টিভেট থাকলে কাজ করবে)
        count = 1
        active_buff = user_data.get("active_buff")
        
        if active_buff == "legendary": count = 10
        elif active_buff == "epic": count = 5
        elif active_buff == "common": count = 2
        
        # একবার ব্যবহারের পর বাফ রিমুভ হবে
        user_data["active_buff"] = None

        inventory = user_data.get("inventory", {})
        inventory[animal] = inventory.get(animal, 0) + count
        user_data["inventory"] = inventory
        
        save_json(data)

        embed = discord.Embed(
            title="🐾 Hunting Success!",
            description=f"আপনি শিকার করে **{animal}** পেয়েছেন!",
            color=0x2ecc71 if category != "Legendary" else 0xf1c40f
        )
        embed.add_field(name="Animal", value=f"### {animal} x{count}", inline=True)
        embed.add_field(name="Category", value=f"`{category}`", inline=True)
        
        if active_buff:
            embed.set_footer(text=f"💎 {active_buff.capitalize()} জেম ব্যবহারের কারণে {count}টি শিকার পেয়েছেন!")
        else:
            embed.set_footer(text=f"১০ ক্যাশ কাটা হয়েছে • নতুন ব্যালেন্স: {user_data['balance']}")
        
        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(name="usegem", description="Activate a gem for your next hunt!")
    async def use_gem(self, ctx, gem_type: str):
        user_id = str(ctx.author.id)
        data = load_json()
        
        gem_type = gem_type.lower()
        if gem_type not in ["common", "epic", "legendary"]:
            return await ctx.send("❌ সঠিক জেম টাইপ লিখুন: `common`, `epic`, অথবা `legendary`", ephemeral=True)
        
        user_data = data.get(user_id)
        if not user_data or user_data.get("gems", {}).get(gem_type, 0) <= 0:
            return await ctx.send(f"❌ আপনার কাছে কোনো `{gem_type}` জেম নেই!", ephemeral=True)

        if user_data.get("active_buff"):
            return await ctx.send(f"⚠️ আপনার অলরেডি একটি জেম এক্টিভেট করা আছে!", ephemeral=True)

        # জেম কমিয়ে বাফ এক্টিভেট করা
        user_data["gems"][gem_type] -= 1
        user_data["active_buff"] = gem_type
        save_json(data)

        await ctx.send(f"💎 **{gem_type.capitalize()} Gem** এক্টিভেট হয়েছে! আপনার পরবর্তী হান্টে আপনি অনেকগুলো এনিমেল পাবেন।")

async def setup(bot):
    await bot.add_cog(HuntSystem(bot))
          
