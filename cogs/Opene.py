import discord
from discord.ext import commands
import random
import json
import os

# হান্ট সিস্টেমের সাথে একই ডাটাবেস ফাইল ব্যবহার করা হচ্ছে
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

class LootboxSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="open", 
        aliases=["op", "lb"], 
        description="Open lootboxes to get Hunt Gems (Common, Epic, Legendary)"
    )
    async def open_box(self, ctx: commands.Context):
        data = load_json()
        user_id = str(ctx.author.id)

        # ১. লুটবক্স চেক
        if user_id not in data or data[user_id].get("lootboxes", 0) <= 0:
            return await ctx.send("❌ You don't have any lootboxes! Get them using `/daily`.", ephemeral=True)

        # ২. Rarity Logic (ক্যাটাগরি অনুযায়ী পাওয়ার চান্স)
        rand = random.random() * 100
        
        if rand <= 5: # ৫% চান্স
            gem_type = "legendary"
            gem_emoji = "💎"
            color = 0xffd700 # Gold
        elif rand <= 30: # ২৫% চান্স (৫ + ২৫ = ৩০)
            gem_type = "epic"
            gem_emoji = "🟣"
            color = 0x9b59b6 # Purple
        else: # ৭০% চান্স
            gem_type = "common"
            gem_emoji = "🔹"
            color = 0x3498db # Blue

        # ৩. ডাটাবেস আপডেট
        data[user_id]["lootboxes"] -= 1
        
        # জেম ফিল্ড চেক ও আপডেট
        if "gems" not in data[user_id]:
            data[user_id]["gems"] = {"common": 0, "epic": 0, "legendary": 0}
            
        data[user_id]["gems"][gem_type] += 1
        save_json(data)

        # ৪. এমবেড ডিজাইন
        embed = discord.Embed(
            title="📦 Lootbox Unboxed!",
            description=f"You opened a lootbox and found a hidden treasure!",
            color=color
        )
        embed.add_field(name="✨ Item Found", value=f"{gem_emoji} **{gem_type.capitalize()} Gem**", inline=True)
        embed.add_field(name="📊 Rarity", value=f"`{self.get_rarity_text(gem_type)}`", inline=True)
        
        embed.add_field(name="🎒 Your Gems", value=(
            f"🔹 Common: `{data[user_id]['gems']['common']}`\n"
            f"🟣 Epic: `{data[user_id]['gems']['epic']}`\n"
            f"💎 Legendary: `{data[user_id]['gems']['legendary']}`"
        ), inline=False)
        
        embed.set_footer(text=f"Remaining Boxes: {data[user_id]['lootboxes']} | Use !usegem to activate")
        
        await ctx.send(embed=embed)

    def get_rarity_text(self, gem_type):
        if gem_type == "legendary": return "LEGENDARY (5%)"
        if gem_type == "epic": return "EPIC (25%)"
        return "COMMON (70%)"

async def setup(bot):
    await bot.add_cog(LootboxSystem(bot))
