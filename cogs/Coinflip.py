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
    async def coin_flip(self, ctx: commands.Context, *, args: str = None):
        if args is None:
            return await ctx.send("❌ Usage: `Wow cf <h/t> <amount>` or `Wow cf <amount>`", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_json(DB_FILE)

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0}
        
        balance = data[user_id]["balance"]
        raw_input = args.lower().strip()

        # --- Side & Amount Detection Logic ---
        user_choice = "heads" # Default side
        bet_amount = 0

        # স্পেস দিয়ে ইনপুট আলাদা করা (যেমন: ['t', '1000'] বা ['all'])
        parts = raw_input.split()
        
        for part in parts:
            if part in ['h', 'heads', 'head']:
                user_choice = "heads"
            elif part in ['t', 'tails', 'tail']:
                user_choice = "tails"
            elif part in ['all', 'max', 'cap']:
                bet_amount = balance
            else:
                # সংখ্যা বা 'k' ডিটেক্ট করা
                match = re.search(r'(\d+)(k)?', part)
                if match:
                    val = int(match.group(1))
                    if match.group(2) == 'k':
                        val *= 1000
                    bet_amount = val

        # --- Validations ---
        if bet_amount <= 0:
            return await ctx.send(f"❌ সঠিক অ্যামাউন্ট লিখুন! উদাহরণ: `Wow cf t 100`", ephemeral=True)
        
        if balance <= 0:
            return await ctx.send(f"❌ আপনার একাউন্টে কোনো টাকা নেই!", ephemeral=True)

        # ম্যাক্স বেট লিমিট চেক (২৫০,০০০)
        actual_bet = min(bet_amount, 250000)
        
        if actual_bet > balance:
            return await ctx.send(f"❌ Low Balance! You have {self.emoji_cash} **{balance:,}**", ephemeral=True)

        # --- Phase 1: Animation Embed ---
        embed = discord.Embed(color=0x2b2d31) 
        embed.description = (
            f"**{ctx.author.display_name}** spent {self.emoji_cash} **{actual_bet:,}** and chose **{user_choice.upper()}**\n\n"
            f"{self.emoji_spinning} **The coin spins...**"
        )
        msg = await ctx.send(embed=embed)
        
        await asyncio.sleep(2)

        # --- Phase 2: Result Logic ---
        actual_result = random.choice(["heads", "tails"])
        is_win = (user_choice == actual_result)
        final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails

        if is_win:
            data[user_id]["balance"] += actual_bet
            status = f"and **won** {self.emoji_cash} **{actual_bet:,}**! 🎉"
            embed.color = 0x2ecc71 
        else:
            data[user_id]["balance"] -= actual_bet
            status = f"and **lost** it all... :("
            embed.color = 0xe74c3c 

        save_json(DB_FILE, data)

        # --- Phase 3: Final Result Embed ---
        embed.description = (
            f"**{ctx.author.display_name}** spent {self.emoji_cash} **{actual_bet:,}** and chose **{user_choice.upper()}**\n\n"
            f"{final_emoji} **The coin spins...** {status}"
        )
        embed.set_footer(text=f"New Balance: {data[user_id]['balance']:,} • Global Economy")
        
        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
    
