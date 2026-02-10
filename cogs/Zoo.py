import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DB_FILE = 'economy.json'

def load_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

class ZooCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ক্যাটাগরি ম্যাপিং (জানার জন্য কোন এনিমেল কোন গ্রুপের)
        self.categories = {
            "Common": ["🐭", "🐹", "🐰", "🐱", "🐶", "🦊", "🐻", "🐼", "🐨", "🐯"],
            "Uncommon": ["🐸", "🐷", "🐮", "🦁", "🐵", "🐒", "🐔", "🐧", "🐦", "🐤"],
            "Rare": ["🦄", "🐴", "🐗", "🦒", "🦓", "🐘", "🦏", "🐫", "🐪", "🦌"],
            "Epic": ["🐍", "🦎", "🦖", "🦕", "🐢", "🐊", "🐙", "🦑", "🐬", "🐳"],
            "Legendary": ["🐉", "🐲", "🦁", "🦅", "豹", "🦈", "🦍", "🦣", "🦦", "🦥"]
        }

    @commands.hybrid_command(name="zoo", aliases=["z", "Zoo", "Z"], description="View your global animal collection!")
    async def zoo(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user_id = str(target.id)
        data = load_json()
        
        user_data = data.get(user_id, {})
        inventory = user_data.get("inventory", {}) # এনিমেল ডাটা
        gems = user_data.get("gems", {"common": 0, "epic": 0, "legendary": 0}) # জেমস ডাটা

        embed = discord.Embed(
            title=f"🐾 {target.name}'s Global Zoo",
            color=0x7289da,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        # --- এনিমেল ডিসপ্লে লজিক ---
        found_any_animal = False
        
        for category, animal_list in self.categories.items():
            display_text = ""
            for animal in animal_list:
                count = inventory.get(animal, 0)
                if count > 0:
                    display_text += f"{animal} `x{count}`  "
            
            if display_text: # যদি এই ক্যাটাগরিতে অন্তত একটি এনিমেল থাকে
                embed.add_field(name=f"━━ {category} ━━", value=display_text, inline=False)
                found_any_animal = True

        if not found_any_animal:
            embed.description = "🌵 This zoo is currently empty. Go hunt some animals!"

        # --- জেমস ডিসপ্লে (যদি থাকে) ---
        gem_text = ""
        if gems.get("common", 0) > 0: gem_text += f"🟤 Common: `{gems['common']}`  "
        if gems.get("epic", 0) > 0: gem_text += f"🟣 Epic: `{gems['epic']}`  "
        if gems.get("legendary", 0) > 0: gem_text += f"🟡 Legendary: `{gems['legendary']}`  "

        if gem_text:
            embed.add_field(name="💎 Available Gems", value=gem_text, inline=False)

        # একটি সুন্দর ফুটার
        embed.set_footer(text=f"Global Economy System • {target.name}", icon_url=self.bot.user.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ZooCommand(bot))
              
