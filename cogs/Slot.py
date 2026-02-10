import discord
from discord.ext import commands
import random
import asyncio
import json
import os

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
        self.cash_emoji = "<:Nova:1453460518764548186>"
        self.spinning_slot = "<a:slot:1470669361155932230>" # আপনার দেওয়া ইমোজি
        # স্লট আইটেমসমূহ
        self.items = ["🍇", "🍒", "🍋", "🍊", "🍎", "💎", "⭐"]

    @commands.hybrid_command(name="slot", aliases=["s", "sl", "S", "Slot"], description="High stakes slots machine!")
    async def slots(self, ctx, amount: str):
        user_id = str(ctx.author.id)
        data = load_json()
        
        if user_id not in data:
            data[user_id] = {"balance": 0}
        
        balance = data[user_id]["balance"]

        # --- Bet Calculation ---
        if amount.lower() == "all":
            bet = min(balance, 100000)
        else:
            try:
                bet = int(amount.replace('k', '000').replace(',', ''))
            except ValueError:
                return await ctx.send("❌ Usage: `Wow slot 100` or `Wow sl all`", ephemeral=True)

        if bet <= 0: return await ctx.send("❌ Invalid bet amount!", ephemeral=True)
        if bet > balance: return await ctx.send(f"❌ You only have {self.cash_emoji} **{balance:,}**", ephemeral=True)
        if bet > 100000: return await ctx.send("🚫 Max bet is **100,000**!", ephemeral=True)

        # Deduct bet
        data[user_id]["balance"] -= bet
        save_json(data)

        # --- Initial Animation Display ---
        # ইমেজের মতো ফরম্যাট: __SLOTS__ এবং স্লট বক্স
        display_slots = f"{self.spinning_slot} {self.spinning_slot} {self.spinning_slot}"
        content = (
            f"**___ SLOTS ___**\n"
            f"║ {display_slots} ║  **{ctx.author.name}** bet {self.cash_emoji} **{bet:,}**\n"
            f"╚═══════╝"
        )
        msg = await ctx.send(content)

        # ফলাফল নির্ধারণ
        # হারার চান্স ৫০% এবং বাকিটা রেন্ডম
        is_loss = random.random() < 0.50
        
        if is_loss:
            # আলাদা ইমোজি দিবে যাতে না মিলে
            final_result = random.sample(self.items, 3)
        else:
            # জেতার চান্স (সবগুলো মিলবে)
            winning_item = random.choice(self.items)
            final_result = [winning_item, winning_item, winning_item]

        # ২ সেকেন্ড পর রেজাল্ট রিভিল
        await asyncio.sleep(2)

        # --- Winning Logic ---
        is_win = final_result[0] == final_result[1] == final_result[2]
        multiplier = 0
        
        if is_win:
            win_item = final_result[0]
            if win_item == "⭐": multiplier = 6
            elif win_item == "💎": multiplier = 4
            elif win_item == "🍎": multiplier = 3
            else: multiplier = 2
            
            winnings = bet * multiplier
            data[user_id]["balance"] += winnings
            save_json(data)
            
            status_text = f"and won {self.cash_emoji} **{winnings:,}** (x{multiplier})"
        else:
            status_text = f"and lost it all... 💀"

        # --- Final Content Update ---
        final_display = f"{final_result[0]} {final_result[1]} {final_result[2]}"
        updated_content = (
            f"**___ SLOTS ___**\n"
            f"║ {final_display} ║  **{ctx.author.name}** bet {self.cash_emoji} **{bet:,}**\n"
            f"╚═══════╝ {status_text}"
        )
        
        await msg.edit(content=updated_content)

async def setup(bot):
    await bot.add_cog(Slots(bot))
    
