import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime

# Database File
DB_FILE = 'economy.json'

def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class DailyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_daily(self, ctx_or_interaction, user):
        data = load_data()
        user_id = str(user.id)
        now = datetime.datetime.now(datetime.timezone.utc)

        # Initialize user data if not exists
        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None}

        user_data = data[user_id]
        last_daily_str = user_data.get("last_daily")
        
        # 24-Hour Cooldown Logic
        if last_daily_str:
            last_daily = datetime.datetime.fromisoformat(last_daily_str)
            if (now - last_daily).total_seconds() < 86400:
                time_left = datetime.timedelta(seconds=86400 - (now - last_daily).total_seconds())
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                msg = f"⏳ You have already claimed your daily reward! Please wait **{hours}h {minutes}m**."
                if isinstance(ctx_or_interaction, discord.Interaction):
                    return await ctx_or_interaction.response.send_message(msg, ephemeral=True)
                else:
                    return await ctx_or_interaction.send(msg)

            # Streak Reset Logic (If more than 48 hours passed)
            if (now - last_daily).total_seconds() > 172800:
                user_data["streak"] = 0

        # Reward Calculation: Day 1 = 800, then +200 each day
        streak = user_data["streak"]
        reward = 800 + (streak * 200)
        
        user_data["balance"] += reward
        user_data["streak"] += 1
        user_data["last_daily"] = now.isoformat()
        
        save_data(data)

        # Professional Dashboard Style Embed
        embed = discord.Embed(
            title="✨ DAILY REWARD CLAIMED ✨",
            description=f"Great job, {user.mention}! You've kept your streak alive.",
            color=0x2ecc71 # Green Color
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="💰 Reward Received", value=f"**{reward}** Coins", inline=True)
        embed.add_field(name="🔥 Current Streak", value=f"**{user_data['streak']}** Days", inline=True)
        embed.add_field(name="🏦 Total Balance", value=f"**{user_data['balance']}** Coins", inline=False)
        
        # Animated Coin/Gift Image for Visual Appeal
        embed.set_image(url="https://i.imgur.com/8NID0vH.gif") 
        embed.set_footer(text="Come back tomorrow to increase your reward!")

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

    # 1. Prefix Command (e.g., !daily)
    @commands.command(name="daily")
    async def daily_prefix(self, ctx):
        await self.process_daily(ctx, ctx.author)

    # 2. Slash Command (e.g., /daily)
    @app_commands.command(name="daily", description="Claim your daily coin reward with a streak bonus!")
    async def daily_slash(self, interaction: discord.Interaction):
        await self.process_daily(interaction, interaction.user)

async def setup(bot):
    await bot.add_cog(DailyCommand(bot))
