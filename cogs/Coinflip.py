import discord
from discord.ext import commands
import random
import asyncio
import json
import os
import re

# --- Global Database Path ---
DB_FILE = 'economy.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class CoinFlip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_spinning = "<a:cf:1434413973759070372>" 
        self.emoji_heads = "<:hade:1453460439898783814>"   
        self.emoji_tails = "<:Tails:1434414186875588639>"
        self.emoji_cash = "<:Nova:1453460518764548186>"   

    @commands.hybrid_command(name="cf", aliases=["coinflip", "flip"], description="Premium CoinFlip Game")
    async def coin_flip(self, ctx: commands.Context, *, args: str = "h 0"):
        user_id = str(ctx.author.id)
        data = load_json(DB_FILE)

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0}
        
        balance = data[user_id]["balance"]
        raw_input = args.lower().replace(',', '')

        # --- Side Detection (Default is Heads) ---
        user_choice = "tails" if 't' in raw_input else "heads"

        # --- Amount Detection ---
        bet_str = "0"
        if "all" in raw_input or "cap" in raw_input:
            bet_str = "all"
        else:
            match = re.search(r'(\d+k|\d+)', raw_input)
            if match: bet_str = match.group(1)

        bet = min(balance, 250000) if bet_str == "all" else int(bet_str.replace('k', '000')) if bet_str.isdigit() or 'k' in bet_str else 0

        # --- Validations ---
        if bet <= 0: return await ctx.send("❌ Usage: `Wow cf t 100` or `Wow cf all`", ephemeral=True)
        if bet > 250000: return await ctx.send("🚫 Max bet limit is **250,000**.", ephemeral=True)
        if bet > balance: return await ctx.send(f"❌ Low Balance! You have {self.emoji_cash} **{balance:,}**", ephemeral=True)

        # --- Phase 1: Animation ---
        # OwO এর মতো সরাসরি টেক্সট দিয়ে শুরু হবে
        msg = await ctx.send(f"🪙 | **{ctx.author.name}** spent {self.emoji_cash} **{bet:,}** and chose **{user_choice.upper()}**\n{self.emoji_spinning} The coin spins...")
        
        await asyncio.sleep(2)

        # --- Phase 2: Result Logic ---
        actual_result = random.choice(["heads", "tails"])
        is_win = (user_choice == actual_result)
        final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails

        if is_win:
            data[user_id]["balance"] += bet
            status = f"and **won** {self.emoji_cash} **{bet:,}**! 🎉"
            embed_color = 0x2ecc71 # Green
        else:
            data[user_id]["balance"] -= bet
            status = f"and **lost** it all... 💀"
            embed_color = 0xe74c3c # Red

        save_json(DB_FILE, data)

        # --- Phase 3: Premium Embed Display ---
        embed = discord.Embed(
            description=f"🪙 | **{ctx.author.name}** spent {self.emoji_cash} **{bet:,}** and chose **{user_choice.upper()}**\nThe coin spins... {final_emoji} {status}",
            color=embed_color
        )
        embed.set_footer(text=f"New Balance: {data[user_id]['balance']:,} • Global Economy")
        
        # মেসেজটি এডিট করে এমবেড দেখানো হবে
        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
