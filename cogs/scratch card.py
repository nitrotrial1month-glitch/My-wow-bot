import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os

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
CARD_COST = 500
SYMBOLS = {
    "jackpot": {"emoji": "👑", "payout": 50000},
    "high":    {"emoji": "💎", "payout": 10000},
    "mid":     {"emoji": "💰", "payout": 5000},
    "low":     {"emoji": "💵", "payout": 2000},
    "trash":   ["🌀", "💩", "💣", "🧱", "🧦"]
}

# --- ১. কাস্টম বাটন ক্লাস ---
class ScratchButton(discord.ui.Button):
    def __init__(self, row, label_emoji):
        super().__init__(style=discord.ButtonStyle.secondary, label="‎", row=row)
        self.hidden_emoji = label_emoji
        self.revealed = False

    async def callback(self, interaction: discord.Interaction):
        view: ScratchView = self.view
        
        # ইউজার চেক
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message(f"❌ **{interaction.user.display_name}**, this is not your card!", ephemeral=True)

        if self.revealed:
            return # অলরেডি রিভিল হলে কিছু করবে না

        # বাটন রিভিল করা
        self.style = discord.ButtonStyle.primary 
        self.emoji = self.hidden_emoji
        self.label = None 
        self.disabled = True
        self.revealed = True
        
        # কাউন্টার বাড়ানো
        view.scratched_count += 1
        
        # সব বাটন স্ক্র্যাচ করা শেষ কিনা চেক করা
        if view.scratched_count == 9:
            await view.end_game(interaction)
        else:
            # গেম চলছে... শুধু বাটন আপডেট হবে
            await interaction.response.edit_message(view=view)

# --- ২. কাস্টম ভিউ ক্লাস ---
class ScratchView(discord.ui.View):
    def __init__(self, ctx, grid, payout, win_symbol, final_balance):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.user_id = ctx.author.id
        self.scratched_count = 0
        self.payout = payout
        self.win_symbol = win_symbol
        self.final_balance = final_balance
        
        # বাটন তৈরি
        for i in range(9):
            button = ScratchButton(row=i // 3, label_emoji=grid[i])
            self.add_item(button)

    async def end_game(self, interaction: discord.Interaction):
        # সব বাটন ডিজেবল করা (যদিও লজিকে অলরেডি ডিজেবল হচ্ছে)
        for child in self.children:
            child.disabled = True

        # রেজাল্ট অনুযায়ী এমবেড সাজানো
        if self.payout > 0:
            color = discord.Color.green()
            title = "🎉 WINNER!"
            desc = f"**Congratulations!**\nYou found 3 {self.win_symbol} symbols!\n\n💰 **Won:** {self.payout:,} coins"
        else:
            color = discord.Color.red()
            title = "💀 Better Luck Next Time"
            desc = "**No match found!**\nTry again to win big."

        embed = discord.Embed(
            title=title,
            description=desc,
            color=color
        )
        embed.set_footer(text=f"New Balance: {self.final_balance:,} coins")
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

# --- ৩. মেইন ক্লাস ---
class Scratch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_card(self):
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

    @commands.hybrid_command(name="scratch", description="🎫 Buy a scratch card with buttons!", aliases=["sc"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def scratch(self, ctx):
        uid = str(ctx.author.id)
        data = load_json(ECO_FILE)
        
        if uid not in data: data[uid] = {"balance": 0}
        
        if data[uid]["balance"] < CARD_COST:
            return await ctx.send(f"❌ You need **{CARD_COST}** coins to play!", ephemeral=True)

        # টাকা কাটা
        data[uid]["balance"] -= CARD_COST
        
        # কার্ড জেনারেট
        grid, payout, win_symbol = self.generate_card()
        
        # জেতার টাকা এখনই যোগ করে সেভ করা (কিন্তু ইউজার দেখবে শেষে)
        if payout > 0:
            data[uid]["balance"] += payout
            
        save_json(ECO_FILE, data)
        final_balance = data[uid]["balance"]

        # শুরুর এমবেড (রেজাল্ট ছাড়া)
        embed = discord.Embed(
            title="🎫 Scratch Card",
            description=f"Cost: **{CARD_COST}** coins\n👇 **Scratch all 9 boxes to see the result!**",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Keep scratching...")

        view = ScratchView(ctx, grid, payout, win_symbol, final_balance)
        await ctx.send(embed=embed, view=view)

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
        
