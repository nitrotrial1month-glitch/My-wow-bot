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

    @commands.hybrid_command(name="cf", aliases=["coinflip", "flip"], description="Global CoinFlip: Bet and choose Heads/Tails!")
    async def coin_flip(self, ctx: commands.Context, *, args: str = "h 0"):
        user_id = str(ctx.author.id)
        data = load_json(DB_FILE)

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None}
        
        balance = data[user_id]["balance"]

        # --- Smart Argument Parsing (Flexible detection) ---
        raw_input = args.lower().replace(',', '')
        
        # Choice ডিটেক্ট করা (h/t)
        user_choice = "heads" # ডিফল্ট
        if 't' in raw_input:
            user_choice = "tails"
        elif 'h' in raw_input:
            user_choice = "heads"

        # অ্যামাউন্ট ডিটেক্ট করা (Regex ব্যবহার করে সংখ্যা বা 'all' বের করা)
        bet_str = "0"
        if "all" in raw_input or "cap" in raw_input:
            bet_str = "all"
        else:
            # ইনপুট থেকে সংখ্যা এবং 'k' খুঁজে বের করা (যেমন: t100 বা 100t থেকে 100 বের করা)
            match = re.search(r'(\d+k|\d+)', raw_input)
            if match:
                bet_str = match.group(1)

        # --- Bet Calculation ---
        bet = 0
        if bet_str == "all":
            bet = min(balance, 250000)
        else:
            try:
                clean_bet = bet_str.replace('k', '000')
                bet = int(clean_bet)
            except ValueError:
                bet = 0

        # --- Validations ---
        if bet <= 0 and bet_str != "all":
            return await ctx.send("❌ Please provide a valid bet amount! Example: `!cf t 100` or `!cf 10k h`", ephemeral=True)
        if bet > 250000:
            return await ctx.send("🚫 **Global Limit:** Max bet is **250,000** coins.", ephemeral=True)
        if bet > balance:
            return await ctx.send(f"❌ **Insufficient Funds!** Balance: {self.emoji_cash} **{balance:,}**", ephemeral=True)

        await ctx.defer() 

        # --- Animation ---
        msg = await ctx.send(f"{self.emoji_spinning} | **{ctx.author.name}** is flipping for **{user_choice.upper()}**...")
        await asyncio.sleep(2)

        # --- Result Logic ---
        actual_result = random.choice(["heads", "tails"])
        is_win = (user_choice == actual_result)

        if is_win:
            data[user_id]["balance"] += bet
            final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails
            result_msg = f"**YOU WON!** 🎉\nReceived: {self.emoji_cash} **{bet:,}**"
            color = discord.Color.green()
        else:
            data[user_id]["balance"] -= bet
            final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails
            result_msg = f"**YOU LOST!** 💀\nLost: {self.emoji_cash} **{bet:,}**"
            color = discord.Color.red()

        save_json(DB_FILE, data)

        # --- Embed ---
        embed = discord.Embed(
            description=f"{final_emoji} | Result: **{actual_result.upper()}**\n{result_msg}",
            color=color
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Choice: {user_choice.upper()} • Balance: {data[user_id]['balance']:,}")
        
        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
    
