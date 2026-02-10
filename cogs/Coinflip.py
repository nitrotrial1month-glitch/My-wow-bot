import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import json
import os

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
        # --- Custom Emojis ---
        self.emoji_spinning = "<a:cf:1434413973759070372>" 
        self.emoji_heads = "<:hade:1453460439898783814>"   
        self.emoji_tails = "<:Tails:1434414186875588639>"
        self.emoji_cash = "<:Nova:1453460518764548186>"   

    @commands.hybrid_command(name="cf", aliases=["coinflip", "flip"], description="Flip a coin! Use 'h' or 't' to choose side.")
    @app_commands.describe(
        amount="Amount to bet (e.g. 10k, all, 500)",
        choice="Heads (h) or Tails (t) - Default is heads"
    )
    async def coin_flip(self, ctx: commands.Context, amount: str = "0", choice: str = "h"):
        user_id = str(ctx.author.id)
        data = load_json(DB_FILE)

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None}
        
        balance = data[user_id]["balance"]
        
        # --- Smart Choice Logic (h/t detection) ---
        user_input = choice.lower()
        if user_input in ["h", "head", "heads"]:
            user_choice = "heads"
        elif user_input in ["t", "tail", "tails"]:
            user_choice = "tails"
        else:
            user_choice = "heads" # Default fallback

        # --- Bet Logic (Cap All) ---
        bet = 0
        if amount.lower() in ["cap", "all"]:
            bet = min(balance, 250000)
        else:
            try:
                clean_amount = amount.lower().replace('k', '000')
                bet = int(clean_amount)
            except ValueError:
                return await ctx.send("❌ **Invalid amount!** Try: `!cf 10k h` or `!cf all t`.", ephemeral=True)

        # --- Validations ---
        if bet < 0:
            return await ctx.send("❌ Negative bets are not allowed!", ephemeral=True)
        if bet > 250000:
            return await ctx.send("🚫 **Bet Limit:** Max **250,000** coins.", ephemeral=True)
        if bet > balance:
            return await ctx.send(f"❌ **Low Balance!** You have {self.emoji_cash} **{balance:,}**", ephemeral=True)

        await ctx.defer() 

        # --- Phase 1: Animation ---
        msg = await ctx.send(f"{self.emoji_spinning} | **{ctx.author.name}** flipped for **{user_choice.upper()}**...")
        
        await asyncio.sleep(2)

        # --- Phase 2: Result ---
        actual_result = random.choice(["heads", "tails"])
        is_win = (user_choice == actual_result)

        if is_win:
            data[user_id]["balance"] += bet
            final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails
            result_msg = f"**YOU WON!** 🎉\nGain: {self.emoji_cash} **{bet:,}**"
            color = discord.Color.green()
        else:
            data[user_id]["balance"] -= bet
            final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails
            result_msg = f"**YOU LOST!** 💀\nLoss: {self.emoji_cash} **{bet:,}**"
            color = discord.Color.red()

        save_json(DB_FILE, data)

        # --- Phase 3: Result Embed ---
        embed = discord.Embed(
            description=f"{final_emoji} | Result: **{actual_result.upper()}**\n{result_msg}",
            color=color
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Bet: {bet:,} • Chosen: {user_choice.upper()} • Balance: {data[user_id]['balance']:,}")
        
        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
