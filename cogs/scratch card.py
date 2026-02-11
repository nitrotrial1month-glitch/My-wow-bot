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

# --- ১. কাস্টম বাটন ক্লাস (প্রতিটি বক্সের জন্য) ---
class ScratchButton(discord.ui.Button):
    def __init__(self, row, label_emoji):
        # শুরুতে বাটনটি ধূসর (Secondary) এবং একটি প্রশ্নবোধক বা খালি থাকবে
        super().__init__(style=discord.ButtonStyle.secondary, label="‎", row=row)
        self.hidden_emoji = label_emoji # এই বাটনের নিচে কি লুকিয়ে আছে
        self.revealed = False

    async def callback(self, interaction: discord.Interaction):
        view: ScratchView = self.view
        
        # শুধু যিনি গেম চালু করেছেন তিনিই স্ক্র্যাচ করতে পারবেন
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("❌ This is not your card!", ephemeral=True)

        # বাটন রিভিল করা
        self.style = discord.ButtonStyle.primary # কালার নীল হয়ে যাবে
        self.emoji = self.hidden_emoji # লুকানো ইমোজি দেখাবে
        self.label = None # লেভেল সরিয়ে দিবে
        self.disabled = True # আর ক্লিক করা যাবে না
        self.revealed = True
        
        # ভিউ আপডেট করা (নতুন বাটন স্টাইল সহ)
        await interaction.response.edit_message(view=view)

# --- ২. কাস্টম ভিউ ক্লাস (পুরো কার্ডের জন্য) ---
class ScratchView(discord.ui.View):
    def __init__(self, user_id, grid):
        super().__init__(timeout=60)
        self.user_id = user_id
        
        # ৯টি বাটন তৈরি করা (৩x৩ গ্রিড)
        for i in range(9):
            # i // 3 দিয়ে রো নির্ধারণ করা হয় (0, 1, 2)
            button = ScratchButton(row=i // 3, label_emoji=grid[i])
            self.add_item(button)

# --- ৩. মেইন ক্লাস ---
class Scratch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_card(self):
        # লজিক আগের মতোই (Weighted Random)
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
        
        # ১. ব্যালেন্স চেক
        if uid not in data: data[uid] = {"balance": 0}
        
        user_bal = data[uid]["balance"]
        if user_bal < CARD_COST:
            return await ctx.send(f"❌ You need **{CARD_COST}** coins to play!", ephemeral=True)

        # ২. টাকা কাটা ও কার্ড জেনারেট
        data[uid]["balance"] -= CARD_COST
        grid, payout, win_symbol = self.generate_card()
        
        # ৩. টাকা জেতার হিসাব (আগেই করে ফেলা হয়)
        if payout > 0:
            data[uid]["balance"] += payout
            footer_text = f"WINNER! You won {payout:,} coins!"
            color = discord.Color.green()
        else:
            footer_text = "Better luck next time!"
            color = discord.Color.red()
            
        save_json(ECO_FILE, data)

        # ৪. এমবেড তৈরি
        embed = discord.Embed(
            title="🎫 Scratch Card",
            description=f"Click the buttons to reveal your prize!\nCost: **{CARD_COST}** coins",
            color=color
        )
        # জেতার মেসেজটি আমরা স্পয়লার করে ফুটারে বা ডেসক্রিপশনে রাখতে পারি
        # অথবা ইউজার স্ক্র্যাচ করার সময় সাসপেন্স রাখতে পারি
        embed.add_field(name="Result", value=f"||{footer_text}||", inline=False)
        embed.set_footer(text=f"New Balance: {data[uid]['balance']:,}")

        # ৫. ভিউ পাঠানো
        view = ScratchView(ctx.author.id, grid)
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
