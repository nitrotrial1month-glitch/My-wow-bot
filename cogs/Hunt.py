import discord
from discord.ext import commands
import random
import json
import os
import asyncio

# --- Global Database Path ---
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
            "common": ["🐭", "🐹", "🐰", "🐱", "🐶", "🦊", "🐻", "🐼", "🐨", "🐯"],
            "uncommon": ["🐸", "🐷", "🐮", "🦁", "🐵", "🐒", "🐔", "🐧", "🐦", "🐤"],
            "rare": ["🦄", "🐴", "🐗", "🦒", "🦓", "🐘", "🦏", "🐫", "🐪", "🦌"],
            "epic": ["🐍", "🦎", "🦖", "🦕", "🐢", "🐊", "🐙", "🦑", "🐬", "🐳"],
            "legendary": ["🐉", "🐲", "🦁", "🦅", "🐆", "🦈", "🦍", "🦣", "🦦", "🦥"]
        }

    @commands.hybrid_command(name="hunt", aliases=["h"], description="Hunt for animals (15s cooldown)")
    @commands.cooldown(1, 15, commands.BucketType.user) # 15-second cooldown added
    async def hunt(self, ctx):
        user_id = str(ctx.author.id)
        data = load_json()

        if user_id not in data:
            data[user_id] = {"balance": 0, "inventory": {}, "gems": {"common": 0, "epic": 0, "legendary": 0}, "active_buff": None}
        
        user_data = data[user_id]
        
        if user_data.get("balance", 0) < 10:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ You need at least 10 {self.cash_emoji} to hunt!", ephemeral=True)

        # Deduct Balance
        user_data["balance"] -= 10
        await ctx.defer()
        
        msg = await ctx.send("🏹 **Searching the wilderness...**")
        await asyncio.sleep(1.2)

        # --- New Probability Logic ---
        # Legendary: 1%, Epic: 3%, Rare: 6%, Uncommon: 20%, Common: 70%
        rand = random.random() * 100
        if rand <= 1: category = "legendary"
        elif rand <= 4: category = "epic"
        elif rand <= 10: category = "rare"
        elif rand <= 30: category = "uncommon"
        else: category = "common"

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

        # --- Embed Design ---
        embed = discord.Embed(color=0x2b2d31)
        header = f"🌿 | **{ctx.author.display_name}** spent 10 {self.cash_emoji} and"
        main_text = f"caught a **{category.upper()}** {animal} **x{count}**!"
        
        embed.description = f"{header}\n{main_text}"
        
        if active_buff:
            embed.set_footer(text=f"💎 Buff Active: {active_buff.capitalize()} Gem applied!")
        else:
            embed.set_footer(text=f"New Balance: {user_data['balance']:,}")

        await msg.edit(content=None, embed=embed)

    # --- Custom Cooldown Message ---
    @hunt.error
    async def hunt_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = f"{error.retry_after:.2f}"
            msg = f"**⏱ | {ctx.author.display_name}**! Slow down and try the command again in **{retry_after}s**"
            
            if ctx.interaction:
                await ctx.interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.send(msg, delete_after=5)

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
        
