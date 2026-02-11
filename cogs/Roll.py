import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os

# File Paths
ECO_FILE = 'economy.json'

def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class Roll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="roll", description="🎲 Bet and roll 1-100 (Roll > 66 to win!)")
    @app_commands.describe(amount="Amount of coins to bet")
    async def roll(self, ctx, amount: int):
        # 1. Validation
        if amount < 50:
            return await ctx.send("❌ Minimum bet is **50** coins.", ephemeral=True)

        data = load_json(ECO_FILE)
        uid = str(ctx.author.id)
        balance = data.get(uid, {}).get("balance", 0)

        if balance < amount:
            return await ctx.send(f"❌ Insufficient balance! You have **{balance:,}** coins.", ephemeral=True)

        # 2. Logic (Roll the dice)
        roll = random.randint(1, 100)
        
        # Deduct money first (Safe betting logic)
        data[uid]["balance"] -= amount
        
        # Determine Outcome
        winnings = 0
        result_type = "lose"
        
        if roll == 100:
            multiplier = 10
            result_type = "jackpot"
            color = discord.Color.gold()
            msg = "👑 **JACKPOT!** PERFECT ROLL!"
        elif roll >= 91:
            multiplier = 4
            result_type = "win"
            color = discord.Color.purple()
            msg = "🔥 **Huge Win!** (4x)"
        elif roll >= 66:
            multiplier = 2
            result_type = "win"
            color = discord.Color.green()
            msg = "✅ **You Won!** (2x)"
        else:
            multiplier = 0
            result_type = "lose"
            color = discord.Color.red()
            msg = "☠️ **You Lost!**"

        # Calculate Winnings
        if multiplier > 0:
            winnings = amount * multiplier
            data[uid]["balance"] += winnings
            
        save_json(ECO_FILE, data)

        # 3. Quest Integration
        # If you have the quest system, this updates it
        quest_cog = self.bot.get_cog("DailyQuests")
        if quest_cog and multiplier > 0: # Only count as "gamble" if they win (optional) or just play
            await quest_cog.update_quest_progress(ctx.author.id, "gamble")

        # 4. Embed Response
        embed = discord.Embed(
            title="🎲 High Roll", 
            description=f"You bet **{amount:,}** coins.", 
            color=color
        )
        embed.add_field(name="🎲 You Rolled", value=f"**{roll}**", inline=True)
        
        if winnings > 0:
            embed.add_field(name="💰 Winnings", value=f"**+{winnings:,}** coins", inline=True)
            embed.set_footer(text="Multiplier: " + str(multiplier) + "x")
        else:
            embed.add_field(name="💸 Loss", value=f"-{amount:,} coins", inline=True)
            embed.set_footer(text="Better luck next time! (Need 66+)")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roll(bot))
          
