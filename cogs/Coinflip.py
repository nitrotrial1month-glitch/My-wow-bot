import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import json
import os

# --- Global Database Path ---
DB_FILE = 'economy.json'

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class CoinFlip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # --- Your Custom Emojis ---
        self.emoji_spinning = "<a:cf:1434413973759070372>" 
        self.emoji_heads = "<:hade:1453460439898783814>"   
        self.emoji_tails = "<:Tails:1434414186875588639>"
        self.emoji_cash = "<:Nova:1453460518764548186>"   

    # @commands.hybrid_command ব্যবহার করলে এটি স্ল্যাশ এবং প্রিফিক্স দুটিতেই কাজ করবে
    @commands.hybrid_command(name="cf", with_app_command=True, aliases=["coinflip", "flip"], description="Flip a coin and bet global coins!")
    @app_commands.describe(amount="Amount to bet (e.g. 10k, all, 500)")
    async def coin_flip(self, ctx: commands.Context, amount: str = "0"):
        user_id = str(ctx.author.id)
        data = load_data()

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None}
        
        balance = data[user_id]["balance"]

        # --- Bet Logic ---
        bet = 0
        if amount.lower() in ["cap", "all"]:
            bet = min(balance, 250000)
        else:
            try:
                clean_amount = amount.lower().replace('k', '000')
                bet = int(clean_amount)
            except ValueError:
                return await ctx.send("❌ **Invalid amount!** Use a number, '10k', or 'all'.", ephemeral=True)

        if bet < 0:
            return await ctx.send("❌ You can't bet negative amounts!", ephemeral=True)
        if bet > 250000:
            return await ctx.send("🚫 **Limit Reached!** Max bet is **250,000** coins.", ephemeral=True)
        if bet > balance:
            return await ctx.send(f"❌ **Insufficient Funds!** Balance: {self.emoji_cash} **{balance:,}**", ephemeral=True)

        # স্ল্যাশ কমান্ডে রেসপন্স করতে defer করা ভালো যাতে ৩ সেকেন্ডের বেশি সময় নিতে পারে
        await ctx.defer() 

        # --- Phase 1: Animation ---
        msg = await ctx.send(f"{self.emoji_spinning} | **{ctx.author.name}** is flipping a global coin...")
        
        await asyncio.sleep(2)

        # --- Phase 2: Result ---
        result = random.choice(["heads", "tails"])
        win = random.choice([True, False]) 

        if win:
            data[user_id]["balance"] += bet
            final_emoji = self.emoji_heads if result == "heads" else self.emoji_tails
            description = f"**YOU WON!** 🎉\nYou gained {self.emoji_cash} **{bet:,}** coins." if bet > 0 else f"It's **{result.upper()}**!"
            color = discord.Color.green()
        else:
            data[user_id]["balance"] -= bet
            final_emoji = self.emoji_heads if result == "heads" else self.emoji_tails
            description = f"**YOU LOST!** 💀\nYou lost {self.emoji_cash} **{bet:,}** coins." if bet > 0 else f"It's **{result.upper()}**!"
            color = discord.Color.red()

        save_data(data)

        # --- Phase 3: Final Embed ---
        embed = discord.Embed(
            description=f"{final_emoji} | Result: **{result.upper()}**\n{description}",
            color=color
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Global Balance: {data[user_id]['balance']:,}")
        
        await msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
              
