import discord
from discord.ext import commands
import json
import os

DB_FILE = 'economy.json'

def load_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

class Inv(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # জেমসের তথ্য (যাতে নামগুলো ইনভেন্টরিতে দেখানো যায়)
        self.gem_names = {
            "F1": "Forest Gem (C)", "F2": "Forest Gem (U)", "F3": "Forest Gem (E)",
            "L1": "Luck Gem (C)", "L2": "Luck Gem (U)", "L3": "Luck Gem (E)",
            "M1": "Mythic Gem (C)", "M2": "Mythic Gem (U)", "M3": "Mythic Gem (E)"
        }

    @commands.hybrid_command(name="inventory", aliases=["inv", "i"], description="Check your items")
    async def inventory(self, ctx):
        data = load_json()
        user_id = str(ctx.author.id)

        if user_id not in data:
            return await ctx.send("🎒 Your inventory is empty!")

        user_data = data[user_id]
        inventory = user_data.get("inventory", {})
        gems = user_data.get("gems", {})

        # প্রাণীদের লিস্ট তৈরি
        animal_list = [f"{emoji} `x{count}`" for emoji, count in inventory.items() if count > 0]
        animals_str = ", ".join(animal_list) if animal_list else "No animals"

        # জেমসের লিস্ট তৈরি
        gem_list = [f"● `{code}` {self.gem_names.get(code, 'Gem')} (x{count})" for code, count in gems.items() if count > 0]
        gems_str = "\n".join(gem_list) if gem_list else "No gems"

        # একটিভ বাফ
        active = user_data.get("active_buff")
        status = f"✅ `{active}` (Uses: {user_data.get('gem_uses', 0)})" if active else "❌ None"

        embed = discord.Embed(title=f"🎒 {ctx.author.name}'s Inventory", color=0x3498db)
        embed.add_field(name="✨ Active Gem", value=status, inline=False)
        embed.add_field(name="📦 Gems", value=gems_str, inline=False)
        embed.add_field(name="🐾 Animals", value=animals_str[:1024], inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inv(bot))
    
