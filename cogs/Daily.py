import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import os
import datetime

# Database Files (এগুলো সব সার্ভারের জন্য একটাই ফাইল থাকবে)
DB_FILE = 'economy.json'
CONFIG_FILE = 'daily_config.json'

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Dashboard Modal ---
class DailyDashboardModal(Modal, title="Daily Command Dashboard"):
    img_input = TextInput(label="Main Image/GIF URL", required=False)
    thumb_input = TextInput(label="Thumbnail URL (Optional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_json(CONFIG_FILE)
        config['image_url'] = self.img_input.value if self.img_input.value else "https://i.imgur.com/8NID0vH.gif"
        config['thumb_url'] = self.thumb_input.value if self.thumb_input.value else None
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message("✅ Global Daily Dashboard updated!", ephemeral=True)

class DailyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily_dashboard", description="Configure daily settings (Admin Only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def daily_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DailyDashboardModal())

    # Hybrid Command: প্রিফিক্স এবং স্ল্যাশ দুটোতেই কাজ করবে
    @commands.hybrid_command(name="daily", description="Claim your global daily reward!")
    async def daily(self, ctx: commands.Context):
        data = load_json(DB_FILE)
        config = load_json(CONFIG_FILE)
        
        # Global Logic: শুধু user.id ব্যবহার করা হচ্ছে
        user_id = str(ctx.author.id)
        now = datetime.datetime.now(datetime.timezone.utc)

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None}

        user_data = data[user_id]
        last_daily_str = user_data.get("last_daily")
        
        # Cooldown check
        if last_daily_str:
            last_daily = datetime.datetime.fromisoformat(last_daily_str)
            if (now - last_daily).total_seconds() < 86400:
                time_left = datetime.timedelta(seconds=86400 - (now - last_daily).total_seconds())
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return await ctx.send(f"⏳ Please wait **{hours}h {minutes}m** before claiming your global reward again!", ephemeral=True)

        # Reward Calculation
        streak = user_data.get("streak", 0)
        reward = 800 + (streak * 200)
        user_data["balance"] += reward
        user_data["streak"] = streak + 1
        user_data["last_daily"] = now.isoformat()
        save_json(DB_FILE, data)

        embed = discord.Embed(
            title="✨ GLOBAL DAILY REWARD ✨", 
            description=f"Congratulations {ctx.author.mention}!", 
            color=0x2ecc71
        )
        embed.add_field(name="💰 Reward", value=f"**{reward:,}** Coins")
        embed.add_field(name="🔥 Streak", value=f"**{user_data['streak']}** Days")
        
        # Cash Emoji (Nova) যোগ করতে চাইলে নিচে line টি ব্যবহার করতে পারেন
        # embed.add_field(name="💳 New Balance", value=f"<:Nova:1453460518764548186> {user_data['balance']:,}")

        img_url = config.get('image_url', "https://i.imgur.com/8NID0vH.gif")
        embed.set_image(url=img_url)
        
        if config.get('thumb_url'):
            embed.set_thumbnail(url=config['thumb_url'])
        
        embed.set_footer(text=f"Global Economy System • {ctx.author.name}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DailyCommand(bot))
    
