import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import os
import datetime

# Database Files
DB_FILE = 'economy.json'
CONFIG_FILE = 'daily_config.json'

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Daily Image Dashboard Modal ---
class DailyDashboardModal(Modal, title="Daily Command Dashboard"):
    img_input = TextInput(
        label="Main Image/GIF URL", 
        placeholder="https://example.com/reward.gif",
        required=False
    )
    thumb_input = TextInput(
        label="Thumbnail URL (Optional)", 
        placeholder="https://example.com/icon.png",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_json(CONFIG_FILE)
        config['image_url'] = self.img_input.value if self.img_input.value else "https://i.imgur.com/8NID0vH.gif"
        config['thumb_url'] = self.thumb_input.value if self.thumb_input.value else None
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message("✅ Daily Command Dashboard updated!", ephemeral=True)

class DailyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily_dashboard", description="Set the image and thumbnail for the daily reward")
    @app_commands.checks.has_permissions(administrator=True)
    async def daily_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DailyDashboardModal())

    async def process_daily(self, ctx_or_interaction, user):
        data = load_json(DB_FILE)
        config = load_json(CONFIG_FILE)
        user_id = str(user.id)
        now = datetime.datetime.now(datetime.timezone.utc)

        # Initialize User Data
        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None}

        user_data = data[user_id]
        last_daily_str = user_data.get("last_daily")
        
        # 24-Hour Cooldown
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

        # Calculation: Day 1 = 800, then +200 each day
        streak = user_data["streak"]
        reward = 800 + (streak * 200)
        
        user_data["balance"] += reward
        user_data["streak"] += 1
        user_data["last_daily"] = now.isoformat()
        
        save_json(DB_FILE, data)

        # Dashboard Config Images
        image_url = config.get('image_url', "https://i.imgur.com/8NID0vH.gif")
        thumb_url = config.get('thumb_url', user.display_avatar.url)

        embed = discord.
        
