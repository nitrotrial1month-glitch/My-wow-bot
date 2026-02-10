import discord
from discord.ext import commands
import random
import asyncio
import json
import os
import re

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
    async def coin_flip(self, ctx: commands.Context, *, args: str = None):
        if not args:
            return await ctx.send(f"❌ Usage: `Wow cf t 100` or `Wow cf all`", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_json(DB_FILE)

        if user_id not in data:
            data[user_id] = {"balance": 0}
        
        balance = data[user_id]["balance"]
        raw_input = args.lower()

        # --- Side Detection (Heads or Tails) ---
        user_choice = "tails" if 't' in raw_input else "heads"

        # --- Amount Detection Fix ---
        bet = 0
        if "all" in raw_input or "cap" in raw_input:
            bet = balance
        else:
            # সংখ্যার সাথে 'k' বা কমা থাকলে তা হ্যান্ডেল করার জন্য
            match = re.search(r'(\d+k|\d+)', raw_input.replace(',', ''))
            if match:
                val = match.group(1)
                if 'k' in val:
                    bet = int(val.replace('k', '')) * 1000
                else:
                    bet = int(val)

        # --- Validations ---
        if bet <= 0: 
            return await ctx.send(f"❌ Usage: `Wow cf t 100` or `Wow cf all`", ephemeral=True)
        
        if balance <= 0:
            return await ctx.send(f"❌ You have no money to bet!", ephemeral=True)

        # Max limit check (আপনি চাইলে এটি সরাতে পারেন)
        if bet > 250000: 
            bet = 250000 
        
        if bet > balance:
            bet = balance # ব্যালেন্সের বেশি বেট ধরলে তা অটো ব্যালেন্সের সমান হয়ে যাবে

        # --- Logic and UI ---
        name = ctx.author.display_name
        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            f"**{name}** spent {self.emoji_cash} **{bet:,}** and chose **{user_choice.upper()}**\n\n"
            f"{self.emoji_spinning} **The coin spins...**"
        )
        msg = await ctx.send(embed=embed)
        
        await asyncio.sleep(2)

        actual_result = random.choice(["heads", "tails"])
        is_win = (user_choice == actual_result)
        final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails

        if is_win:
            data[user_id]["balance"] += bet
            status = f"and **won** {self.emoji_cash} **{bet:,}**! 🎉"
            embed.color = 0x2ecc71
        else:
            data[user_id]["balance"] -= bet
            status = f"and **lost** it all... 💀"
            embed.color = 0xe74c3c

        save_json(DB_FILE, data)

        embed.description = (
            f"**{name}** spent {self.emoji_cash} **{bet:,}** and chose **{user_choice.upper()}**\n\n"
            f"{final_emoji} **The coin spins...** {status}"
        )
        embed.set_footer(text=f"New Balance: {data[user_id]['balance']:,}")
        
        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
