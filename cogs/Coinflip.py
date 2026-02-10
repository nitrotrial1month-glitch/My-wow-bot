import discord
from discord.ext import commands
from discord import app_commands
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

    @commands.hybrid_command(name="cf", aliases=["coinflip", "flip"], description="Global CoinFlip: Default is Heads if not specified.")
    async def coin_flip(self, ctx: commands.Context, *, args: str = "h 0"):
        user_id = str(ctx.author.id)
        data = load_json(DB_FILE)

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None}
        
        balance = data[user_id]["balance"]
        raw_input = args.lower().replace(',', '')

        # --- সাইড ডিটেকশন লজিক (Default is Heads) ---
        if 't' in raw_input:
            user_choice = "tails"
        else:
            user_choice = "heads" # 'h' থাকুক বা না থাকুক, 't' না থাকলে Heads

        # --- অ্যামাউন্ট ডিটেকশন লজিক (Smart Regex) ---
        bet_str = "0"
        if "all" in raw_input or "cap" in raw_input:
            bet_str = "all"
        else:
            # ইনপুট থেকে সংখ্যা এবং 'k' খুঁজে বের করা
            match = re.search(r'(\d+k|\d+)', raw_input)
            if match:
                bet_str = match.group(1)

        # --- বেট ক্যালকুলেশন ---
        bet = 0
        if bet_str == "all":
            bet = min(balance, 250000)
        else:
            try:
                clean_bet = bet_str.replace('k', '000')
                bet = int(clean_bet)
            except ValueError:
                bet = 0

        # --- ভ্যালিডেশন ---
        if bet <= 0 and bet_str != "all":
            return await ctx.send("❌ Please provide a valid amount! (e.g., `!cf 100`, `!cf t 10k`)", ephemeral=True)
        
        if bet > 250000:
            return await ctx.send("🚫 **Limit:** Max bet is **250,000** coins.", ephemeral=True)
        
        if bet > balance:
            return await ctx.send(f"❌ **Low Balance!** You have {self.emoji_cash} **{balance:,}**", ephemeral=True)

        await ctx.defer() 

        # --- Phase 1: Animation ---
        msg = await ctx.send(f"{self.emoji_spinning} | **{ctx.author.name}** is flipping for **{user_choice.upper()}**...")
        await asyncio.sleep(2)

        # --- Phase 2: Result ---
        actual_result = random.choice(["heads", "tails"])
        is_win = (user_choice == actual_result)

        if is_win:
            data[user_id]["balance"] += bet
            final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails
            result_text = f"**WINNER!** 🎉\nGain: {self.emoji_cash} **{bet:,}**"
            color = discord.Color.green()
        else:
            data[user_id]["balance"] -= bet
            final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails
            result_text = f"**LOST!** 💀\nLoss: {self.emoji_cash} **{bet:,}**"
            color = discord.Color.red()

        save_json(DB_FILE, data)

        # --- Phase 3: Display ---
        embed = discord.Embed(
            description=f"{final_emoji} | Result: **{actual_result.upper()}**\n{result_text}",
            color=color
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Global Balance: {data[user_id]['balance']:,} • Choice: {user_choice.upper()}")
        
        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
    
