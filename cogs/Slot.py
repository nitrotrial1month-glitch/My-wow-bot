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
        self.spinning = "<a:slot:1470669361155932230>" # আপনার দেওয়া এনিমেটেড ইমোজি
        self.items = ["🍇", "🍒", "🍋", "🍊", "🍎", "💎", "⭐"]

    @commands.hybrid_command(name="slot", aliases=["s", "sl", "S", "Slot"])
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
                return await ctx.send("❌ Usage: `Wow sl 100`", ephemeral=True)

        if bet <= 0 or bet > balance:
            return await ctx.send("❌ Invalid balance or bet!", ephemeral=True)

        # Deduct bet
        data[user_id]["balance"] -= bet
        save_json(data)

        # --- Probability Logic ---
        is_loss = random.random() < 0.50 # ৫০% হারার চান্স
        if is_loss:
            final_result = random.sample(self.items, 3)
        else:
            winning_item = random.choice(self.items)
            final_result = [winning_item, winning_item, winning_item]

        # --- Initial Embed Display ---
        embed = discord.Embed(title="🎰 SLOTS 🎰", color=0x5865F2)
        embed.description = (
            f"**___ SLOTS ___**\n"
            f"║ {self.spinning} {self.spinning} {self.spinning} ║  **{ctx.author.display_name}** bet {self.cash_emoji} **{bet:,}**\n"
            f"╚═══════╝\n"
            f"**Spinning...**"
        )
        msg = await ctx.send(embed=embed)

        # --- Sequential Reveal (ধাপে ধাপে রিভিল) ---
        current_slots = [self.spinning, self.spinning, self.spinning]
        
        for i in range(3):
            await asyncio.sleep(2) # ২ সেকেন্ড বিরতি
            current_slots[i] = final_result[i]
            
            embed.description = (
                f"**___ SLOTS ___**\n"
                f"║ {' '.join(current_slots)} ║  **{ctx.author.display_name}** bet {self.cash_emoji} **{bet:,}**\n"
                f"╚═══════╝\n"
                f"**Revealing...**"
            )
            await msg.edit(embed=embed)

        # --- Final Logic ---
        is_win = final_result[0] == final_result[1] == final_result[2]
        
        if is_win:
            win_item = final_result[0]
            if win_item == "⭐": mult = 6
            elif win_item == "💎": mult = 4
            elif win_item == "🍎": mult = 3
            else: mult = 2
            
            winnings = bet * mult
            data[user_id]["balance"] += winnings
            save_json(data)
            
            embed.color = 0x2ecc71
            status = f"and won {self.cash_emoji} **{winnings:,}** (x{mult}) 🎉"
        else:
            embed.color = 0xe74c3c
            status = "and lost it all... 💀"

        embed.description = (
            f"**___ SLOTS ___**\n"
            f"║ {' '.join(final_result)} ║  **{ctx.author.name}** bet {self.cash_emoji} **{bet:,}**\n"
            f"╚═══════╝ {status}"
        )
        embed.set_footer(text=f"New Balance: {data[user_id]['balance']:,}")
        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Slots(bot))
    
