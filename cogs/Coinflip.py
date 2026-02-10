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
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def coin_flip(self, ctx: commands.Context, *, args: str = None):
        if not args:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Usage: `Wow cf t 100` or `Wow cf all`", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_json(DB_FILE)

        if user_id not in data:
            data[user_id] = {"balance": 0}
        
        balance = data[user_id]["balance"]
        raw_input = args.lower().strip()

        # Side Detection
        user_choice = "tails" if re.search(r'\bt\b|\btails\b', raw_input) else "heads"

        # Amount Detection
        bet = 0
        if "all" in raw_input or "cap" in raw_input:
            bet = min(balance, 250000)
        else:
            match = re.search(r'\d+', raw_input)
            if match:
                bet = int(match.group())

        # Validations
        if bet <= 0: 
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ Enter a valid amount! Your balance: {self.emoji_cash} **{balance:,}**", ephemeral=True)
        
        if bet > 250000: 
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("🚫 Max bet limit is **250,000**.", ephemeral=True)
            
        if balance < bet: 
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ Low Balance! You have {self.emoji_cash} **{balance:,}**", ephemeral=True)

        # Phase 1: Animation Embed
        embed = discord.Embed(color=0x2b2d31) 
        embed.description = (
            f"**{ctx.author.display_name}** spent {self.emoji_cash} **{bet:,}** and chose **{user_choice.upper()}**\n\n"
            f"{self.emoji_spinning} **The coin spins...**"
        )
        msg = await ctx.send(embed=embed)
        
        await asyncio.sleep(2)

        # Phase 2: Result Logic
        actual_result = random.choice(["heads", "tails"])
        is_win = (user_choice == actual_result)
        final_emoji = self.emoji_heads if actual_result == "heads" else self.emoji_tails

        if is_win:
            data[user_id]["balance"] += bet
            status = f"and **won** {self.emoji_cash} **{bet:,}**! 🎉"
            embed.color = 0x2ecc71 
        else:
            data[user_id]["balance"] -= bet
            status = f"and **lost** it all... :("
            embed.color = 0xe74c3c 

        save_json(DB_FILE, data)

        # Phase 3: Final Result
        embed.description = (
            f"**{ctx.author.display_name}** spent {self.emoji_cash} **{bet:,}** and chose **{user_choice.upper()}**\n\n"
            f"{final_emoji} **The coin spins...** {status}"
        )
        embed.set_footer(text=f"New Balance: {data[user_id]['balance']:,} • Global Economy")
        
        await msg.edit(embed=embed)

    # --- Cooldown Error Handler ---
    @coin_flip.error
    async def cf_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = f"{error.retry_after:.2f}"
            # Custom requested format
            msg = f"**⏱ | {ctx.author.display_name}**! Slow down and try the command again in **{retry_after}s**"
            
            if ctx.interaction:
                await ctx.interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx.send(msg, delete_after=5)

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))
