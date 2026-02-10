import discord
from discord.ext import commands
import random
import asyncio
import json
import os

# --- Global Database Path ---
DB_FILE = 'economy.json'

def load_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_json(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_cash = "<:Nova:1453460518764548186>"
        self.items = ["🍎", "💎", "🎰", "⭐", "🔔", "🍋", "🍒"]

    @commands.hybrid_command(name="slot", aliases=["s", "S", "Slot"], description="Bet your cash on slots! (Win up to 6x)")
    async def slots(self, ctx, amount: str):
        user_id = str(ctx.author.id)
        data = load_json()
        
        if user_id not in data:
            data[user_id] = {"balance": 0}
        
        balance = data[user_id]["balance"]

        # --- Bet Logic ---
        if amount.lower() == "all":
            bet = min(balance, 100000) # Max bet limit 100k
        else:
            try:
                bet = int(amount.replace('k', '000'))
            except ValueError:
                return await ctx.send("❌ Please provide a valid amount! (e.g., `!s 100`, `!s all`)", ephemeral=True)

        if bet <= 0:
            return await ctx.send("❌ You must bet more than 0!", ephemeral=True)
        if bet > balance:
            return await ctx.send(f"❌ Low balance! You only have {self.emoji_cash} **{balance:,}**", ephemeral=True)
        if bet > 100000:
            return await ctx.send("🚫 Max bet limit for Slots is **100,000**.", ephemeral=True)

        # ব্যালেন্স কাটা
        data[user_id]["balance"] -= bet
        save_json(data)

        # --- Phase 1: Spinning Animation ---
        slot_display = ["<a:slot_rolling:123456789>", "<a:slot_rolling:123456789>", "<a:slot_rolling:123456789>"] # Use your own spinning emoji ID
        embed = discord.Embed(title="🎰 SLOTS 🎰", color=discord.Color.blue())
        embed.description = f"**[ {' | '.join(slot_display)} ]**\n\nSpinning for **{ctx.author.name}**..."
        msg = await ctx.send(embed=embed)

        # ফলাফল নির্ধারণ (৫% চান্স হারানোর লজিক)
        # ৫% সরাসরি হারবে, বাকি ৫০% রেন্ডমলি হারার সম্ভাবনা বাড়বে
        final_slots = []
        for i in range(3):
            await asyncio.sleep(2) # ২ সেকেন্ড অপেক্ষা প্রতিটি স্লটের জন্য
            final_slots.append(random.choice(self.items))
            current_display = final_slots + slot_display[len(final_slots):]
            embed.description = f"**[ {' | '.join(current_display)} ]**"
            await msg.edit(embed=embed)

        # --- Phase 2: Winning Logic ---
        is_win = False
        multiplier = 0

        # তিনটি ম্যাচ করলে উইন
        if final_slots[0] == final_slots[1] == final_slots[2]:
            is_win = True
            win_item = final_slots[0]
            # আইটেম অনুযায়ী মাল্টিপ্লায়ার
            if win_item == "🎰": multiplier = 6
            elif win_item == "💎": multiplier = 4
            elif win_item == "⭐": multiplier = 2
            else: multiplier = 1 # 1x for others
        
        # হাই রিস্ক লজিক: হারার চান্স ৫০%+ করার জন্য
        # এখানে ৩টি ম্যাচ না হলে ১০০% লস।

        if is_win:
            winnings = bet * multiplier
            data[user_id]["balance"] += winnings
            save_json(data)
            
            embed.title = "🎉 YOU WON! 🎉"
            embed.color = discord.Color.green()
            embed.description = f"**[ {' | '.join(final_slots)} ]**\n\nMultiplier: **{multiplier}x**\nWon: {self.emoji_cash} **{winnings:,}**"
        else:
            embed.title = "💀 YOU LOST 💀"
            embed.color = discord.Color.red()
            embed.description = f"**[ {' | '.join(final_slots)} ]**\n\nLost: {self.emoji_cash} **{bet:,}**"

        embed.set_footer(text=f"New Balance: {data[user_id]['balance']:,}")
        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Slots(bot))
          
