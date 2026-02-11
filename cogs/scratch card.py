import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import asyncio

# ফাইল পাথ
ECO_FILE = 'economy.json'

def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- কনফিগারেশন ---
CARD_COST = 500  # কার্ডের দাম
SYMBOLS = {
    "jackpot": {"emoji": "👑", "payout": 50000},
    "high":    {"emoji": "💎", "payout": 10000},
    "mid":     {"emoji": "💰", "payout": 5000},
    "low":     {"emoji": "💵", "payout": 2000},
    "trash":   ["🌀", "💩", "💣", "🧱", "🧦"]
}

class Scratch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_card(self):
        # 1% Jackpot, 5% High, 15% Mid, 30% Low, 49% Lose
        outcome = random.choices(
            ["jackpot", "high", "mid", "low", "lose"], 
            weights=[1, 5, 15, 30, 49], 
            k=1
        )[0]

        grid = []
        win_emoji = None
        payout = 0

        if outcome == "lose":
            trash_pool = SYMBOLS["trash"] * 3
            random.shuffle(trash_pool)
            grid = trash_pool[:9]
        else:
            win_data = SYMBOLS[outcome]
            win_emoji = win_data["emoji"]
            payout = win_data["payout"]
            
            grid = [win_emoji] * 3
            trash_fill = random.choices(SYMBOLS["trash"], k=6)
            grid.extend(trash_fill)
            random.shuffle(grid)

        return grid, payout, win_emoji

    @commands.hybrid_command(name="scratch", description="🎫 Buy a scratch card for 500 coins", aliases=["sc"])
    @commands.cooldown(1, 15, commands.BucketType.user) # ১৫ সেকেন্ড কুলডাউন
    async def scratch(self, ctx):
        uid = str(ctx.author.id)
        data = load_json(ECO_FILE)
        
        # ব্যালেন্স চেক
        user_bal = data.get(uid, {}).get("balance", 0)
        if user_bal < CARD_COST:
            return await ctx.send(f"❌ You need **{CARD_COST}** coins to buy a scratch card!", ephemeral=True)

        # টাকা কেটে নেওয়া
        data[uid]["balance"] -= CARD_COST
        
        # কার্ড জেনারেট
        grid, payout, win_symbol = self.generate_card()
        
        # রেজাল্ট প্রসেসিং (লুকানো থাকবে)
        if payout > 0:
            data[uid]["balance"] += payout
            # রেজাল্ট স্পয়লার ট্যাগের ভেতরে
            result_msg = f"||🎉 **WINNER!** Found 3 {win_symbol}!\n💰 Won: **{payout:,}** coins||"
            color = discord.Color.green()
        else:
            result_msg = "||💩 **Better luck next time!**\nNo matching symbols found.||"
            color = discord.Color.red()
            
        save_json(ECO_FILE, data)

        # গ্রিড সাজানো
        row1 = f"|| {grid[0]} || || {grid[1]} || || {grid[2]} ||"
        row2 = f"|| {grid[3]} || || {grid[4]} || || {grid[5]} ||"
        row3 = f"|| {grid[6]} || || {grid[7]} || || {grid[8]} ||"

        embed = discord.Embed(
            title="🎫 Lucky Scratch Card", 
            description=f"Cost: **{CARD_COST}** coins\n\n{row1}\n{row2}\n{row3}\n\n👇 **Scratch below for Result:**\n{result_msg}",
            color=color
        )
        embed.set_footer(text=f"New Balance: {data[uid]['balance']:,}")

        await ctx.send(embed=embed)

    # --- কুলডাউন এরর হ্যান্ডলার ---
    @scratch.error
    async def scratch_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            time_left = round(error.retry_after, 1)
            embed = discord.Embed(
                description=f"⏳ **{ctx.author.display_name}**, please wait **{time_left}s** before scratching again!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=time_left)
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Scratch(bot))
    
