import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime
import random
import asyncio

# File Paths
ECO_FILE = 'economy.json'
LOTTERY_FILE = 'lottery_data.json'

def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Confirmation View ---
class LotteryConfirmView(discord.ui.View):
    def __init__(self, user_id, amount, eco_data):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.amount = amount
        self.eco_data = eco_data

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This is not your menu!", ephemeral=True)
        
        uid = str(self.user_id)
        if self.eco_data[uid]["balance"] < self.amount:
            return await interaction.response.send_message("❌ You no longer have enough coins!", ephemeral=True)
            
        # Deduct Money
        self.eco_data[uid]["balance"] -= self.amount
        save_json(ECO_FILE, self.eco_data)

        # Register in Lottery
        lottery_data = load_json(LOTTERY_FILE)
        current_bet = lottery_data["participants"].get(uid, 0)
        lottery_data["participants"][uid] = current_bet + self.amount
        lottery_data["pot"] += self.amount
        save_json(LOTTERY_FILE, lottery_data)
        
        await interaction.response.edit_message(
            content=f"✅ **Success!** You entered **{self.amount:,}** coins into the lottery.\n⏳ Results will be sent via DM in 24h.", 
            view=None, embed=None
        )
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This is not your menu!", ephemeral=True)
            
        await interaction.response.edit_message(content="❌ **Transaction Cancelled.** No coins were deducted.", view=None, embed=None)
        self.stop()

class LotterySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lottery_loop.start()

    def cog_unload(self):
        self.lottery_loop.cancel()

    @tasks.loop(minutes=1)
    async def lottery_loop(self):
        data = load_json(LOTTERY_FILE)
        if not data:
            next_draw = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
            data = {"end_time": next_draw.isoformat(), "participants": {}, "pot": 0}
            save_json(LOTTERY_FILE, data)
            return

        end_time = datetime.datetime.fromisoformat(data["end_time"])
        if datetime.datetime.now(datetime.timezone.utc) >= end_time:
            await self.draw_winner(data)

    async def draw_winner(self, data):
        participants = data["participants"]
        pot = data["pot"]

        if not participants:
            next_draw = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
            data["end_time"] = next_draw.isoformat()
            save_json(LOTTERY_FILE, data)
            return

        winner_id = random.choices(list(participants.keys()), weights=list(participants.values()), k=1)[0]
        
        eco_data = load_json(ECO_FILE)
        if winner_id in eco_data:
            eco_data[winner_id]["balance"] += pot
            save_json(ECO_FILE, eco_data)

        winner_name = "Unknown"
        try:
            winner_user = await self.bot.fetch_user(int(winner_id))
            winner_name = winner_user.name
        except: pass

        for uid in participants.keys():
            try:
                user = await self.bot.fetch_user(int(uid))
                if uid == winner_id:
                    await user.send(f"🎉 **JACKPOT!** You won the lottery!\n💰 Prize: **{pot:,}** coins added to your balance.")
                else:
                    await user.send(f"😔 **Lottery Results:**\nYou didn't win this time.\n🏆 Winner: **{winner_name}**\n💰 Total Pot: {pot:,} coins.\nTry again tomorrow!")
            except: pass

        next_draw = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        save_json(LOTTERY_FILE, {"end_time": next_draw.isoformat(), "participants": {}, "pot": 0})

    # --- Commands ---
    @commands.hybrid_command(name="lottery", description="🎟️ Buy a lottery ticket", aliases=["lot", "lotto"])
    @app_commands.describe(amount="Amount of coins to bet")
    async def lottery(self, ctx, amount: int):
        if amount < 100:
            return await ctx.send("❌ Minimum bet is **100** coins.", ephemeral=True)

        eco_data = load_json(ECO_FILE)
        user_bal = eco_data.get(str(ctx.author.id), {}).get("balance", 0)
        
        if user_bal < amount:
            return await ctx.send(f"❌ Insufficient balance! (You have: {user_bal:,})", ephemeral=True)

        lot_data = load_json(LOTTERY_FILE)
        end_time = datetime.datetime.fromisoformat(lot_data["end_time"])
        
        embed = discord.Embed(title="🎟️ Lottery Entry", color=discord.Color.blue())
        embed.description = (
            f"You are betting **{amount:,}** coins.\n"
            f"💰 New Total Pot: **{lot_data['pot'] + amount:,}**\n"
            f"⏳ Drawing in: <t:{int(end_time.timestamp())}:R>\n\n"
            f"Confirm below to register your name."
        )
        
        view = LotteryConfirmView(ctx.author.id, amount, eco_data)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="lot_status", description="📊 View current lottery stats")
    async def lot_status(self, ctx):
        data = load_json(LOTTERY_FILE)
        if not data: return await ctx.send("No lottery running.")

        end_time = datetime.datetime.fromisoformat(data["end_time"])
        my_bet = data["participants"].get(str(ctx.author.id), 0)
        chance = f"{(my_bet / data['pot'] * 100):.1f}%" if data["pot"] > 0 else "0%"

        embed = discord.Embed(title="📊 Global Lottery Stats", color=discord.Color.gold())
        embed.add_field(name="💰 Pot Size", value=f"**{data['pot']:,}**", inline=True)
        embed.add_field(name="⏳ Draw Time", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.add_field(name="🎲 Your Chance", value=f"**{chance}** ({my_bet:,} bet)", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LotterySystem(bot))
      
