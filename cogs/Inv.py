import discord
from discord.ext import commands
import json
import os

# Database Path (Same as your hunt system)
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
        # জেমসের নামগুলো প্রদর্শনের জন্য
        self.gem_names = {
            "F1": "Forest Gem (Common)", "F2": "Forest Gem (Uncommon)", "F3": "Forest Gem (Epic)",
            "L1": "Luck Gem (Common)", "L2": "Luck Gem (Uncommon)", "L3": "Luck Gem (Epic)",
            "M1": "Mythic Gem (Common)", "M2": "Mythic Gem (Uncommon)", "M3": "Mythic Gem (Epic)"
        }

    @commands.hybrid_command(name="inventory", aliases=["inv", "i"], description="Check your gems and animals")
    async def inventory(self, ctx):
        data = load_json()
        user_id = str(ctx.author.id)

        if user_id not in data:
            return await ctx.send(f"🎒 **{ctx.author.display_name}**, your inventory is empty!")

        user_data = data[user_id]
        inventory = user_data.get("inventory", {})
        gems = user_data.get("gems", {})
        active_buff = user_data.get("active_buff")
        gem_uses = user_data.get("gem_uses", 0)

        # ১. এনিমেল সেকশন সাজানো
        animal_list = [f"{emoji} `x{count}`" for emoji, count in inventory.items() if count > 0]
        animals_display = ", ".join(animal_list) if animal_list else "No animals caught yet."

        # ২. জেমস সেকশন সাজানো
        gem_list = []
        if gems:
            for code, count in gems.items():
                if count > 0:
                    name = self.gem_names.get(code, "Unknown Gem")
                    gem_list.append(f"● `{code}` **{name}** (Stock: {count})")
        
        gems_display = "\n".join(gem_list) if gem_list else "No gems in stock."

        # ৩. একটিভ বাফ স্ট্যাটাস
        if active_buff:
            buff_status = f"✅ `{active_buff}` **Active**\n🔋 Remaining Uses: `{gem_uses}`"
        else:
            buff_status = "❌ No gem active"

        # ৪. এমবেড ডিজাইন
        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s Inventory",
            color=0x3498db
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        embed.add_field(name="✨ Active Buff", value=buff_status, inline=False)
        embed.add_field(name="📦 Your Gems", value=gems_display, inline=False)
        embed.add_field(name="🐾 Animals", value=animals_display[:1024], inline=False)
        
        # ব্যালেন্স এবং লুটবক্স তথ্য
        balance = user_data.get('balance', 0)
        lootboxes = user_data.get('lootboxes', 0)
        embed.set_footer(text=f"Balance: {balance:,} | Lootboxes: {lootboxes}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inv(bot))
