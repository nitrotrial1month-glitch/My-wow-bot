import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime
import random

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

# --- Confirmation View with Submission Embed ---
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
        new_total_submission = current_bet + self.amount
        
        lottery_data["participants"][uid] = new_total_submission
        lottery_data["pot"] += self.amount
        save_json(LOTTERY_FILE, lottery_data)

        # --- Calculate Data for Embed ---
        pot = lottery_data["pot"]
        chance = (new_total_submission / pot) * 100 if pot > 0 else 0
        end_time = datetime.datetime.fromisoformat(lottery_data["end_time"])
        time_left = end_time - datetime.datetime.now(datetime.timezone.utc)
        
        # Time Formatting (17h 5m 14s style)
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours}h {minutes}m {seconds}s"

        # --- Create Submission Embed (Like the image) ---
        embed = discord.Embed(
            title=f"『OWNER』 ☯️{interaction.user.name.upper()}』👑's Lottery Submission",
            description="Lottery ends once a day! The maximum lottery submission is **Unlimited**!",
            color=discord.Color.from_rgb(43, 45, 49) # Dark Discord Theme Color
        )
        
        embed.add_field(name="You added", value=f"```yaml\n{self.amount:,} Coins\n```", inline=False)
        embed.add_field(name="Your Total Submission", value=f"```yaml\n{new_total_submission:,} Coins\n```", inline=False)
        embed.add_field(name="Winning Chance", value=f"```yaml\n{chance:.16f}%\n```", inline=False)
        embed.add_field(name="Current Jackpot", value=f"```yaml\n{pot:,} Coins\n```", inline=False)
        embed.add_field(name="Ends in", value=f"```yaml\n{time_str}\n```", inline=False)
        
        embed.set_footer(text="*Percentage and jackpot may change over time")
        embed.timestamp = datetime.datetime.now()

        await interaction.response.edit_message(content=None, embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This is not your menu!", ephemeral=True)
            
        await interaction.response.edit_message(content="❌ **Transaction Cancelled.** No coins were deducted.", view=None, embed=None)
        self.stop()

# --- Lottery System Cog (Keep as it was) ---
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
                    await user.send(f"🎉 **JACKPOT!** You won the lottery!\n💰 Prize: **{pot:,}** coins.")
                else:
                    await user.send(f"😔 **Lottery Results:** Winner: **{winner_name}** | Pot: {pot:,} coins.")
            except: pass

        next_draw = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        save_json(LOTTERY_FILE, {"end_time": next_draw.isoformat(), "participants": {}, "pot": 0})

    @commands.hybrid_command(name="lottery", description="🎟️ Buy a lottery ticket", aliases=["lot"])
    @app_commands.describe(amount="Amount of coins to bet")
    async def lottery(self, ctx, amount: int):
        if amount < 100:
            return await ctx.send("❌ Minimum bet is **100** coins.", ephemeral=True)

        eco_data = load_json(ECO_FILE)
        user_bal = eco_data.get(str(ctx.author.id), {}).get("balance", 0)
        
        if user_bal < amount:
            return await ctx.send(f"❌ Insufficient balance!", ephemeral=True)

        lot_data = load_json(LOTTERY_FILE)
        end_time = datetime.datetime.fromisoformat(lot_data["end_time"])
        
        embed = discord.Embed(title="🎟️ Lottery Entry", color=discord.Color.blue())
        embed.description = f"Betting **{amount:,}** coins. Confirm to register."
        
        view = LotteryConfirmView(ctx.author.id, amount, eco_data)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(LotterySystem(bot))
            
