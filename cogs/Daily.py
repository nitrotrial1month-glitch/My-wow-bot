import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import os
import datetime
import random
# আপনার utils থেকে প্রিমিয়াম ডেটা চেক করার জন্য ইম্পোর্ট
from utils import load_config 

# Database Files
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

# --- প্রিমিয়াম চেক ফাংশন ---
def is_premium(user_id):
    config = load_config() #
    premium_data = config.get("premium", {})
    if str(user_id) in premium_data:
        expiry_str = premium_data[str(user_id)]
        expiry = datetime.datetime.fromisoformat(expiry_str)
        # সময় শেষ হয়েছে কি না চেক
        return datetime.datetime.now() < expiry
    return False

class DailyDashboardModal(Modal, title="Daily Command Dashboard"):
    img_input = TextInput(label="Main Image/GIF URL", required=False)
    thumb_input = TextInput(label="Thumbnail URL (Optional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_json(CONFIG_FILE)
        config['image_url'] = self.img_input.value if self.img_input.value else "https://cdn.discordapp.com/attachments/1439489026225868892/1470689376060313683/daily-22-15001.gif"
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

    @commands.hybrid_command(name="daily", description="Claim your global daily reward and lootboxes!")
    async def daily(self, ctx: commands.Context):
        data = load_json(DB_FILE)
        config = load_json(CONFIG_FILE)
        
        user_id = str(ctx.author.id)
        now = datetime.datetime.now(datetime.timezone.utc)

        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None, "lootboxes": 0}
        
        user_data = data[user_id]
        last_daily_str = user_data.get("last_daily")
        
        # Cooldown check
        if last_daily_str:
            last_daily = datetime.datetime.fromisoformat(last_daily_str)
            if (now.timestamp() - last_daily.timestamp()) < 86400:
                time_left = datetime.timedelta(seconds=86400 - (now.timestamp() - last_daily.timestamp()))
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return await ctx.send(f"⏳ Please wait **{hours}h {minutes}m** before claiming your rewards again!", ephemeral=True)

        # --- Premium Logic Integration ---
        user_is_premium = is_premium(ctx.author.id)
        
        streak = user_data.get("streak", 0)
        base_reward = 800 + (streak * 200)
        
        # প্রিমিয়াম হলে ৫ গুণ রিওয়ার্ড এবং বেশি লুটবক্স
        if user_is_premium:
            reward = base_reward * 5
            boxes_found = random.randint(5, 10) # প্রিমিয়াম মেম্বাররা ৫-১০টি বক্স পাবে
            status_text = "🌟 **PREMIUM USER (5x Bonus)**"
        else:
            reward = base_reward
            boxes_found = random.randint(1, 3) # সাধারণ মেম্বাররা ১-৩টি বক্স পাবে
            status_text = "👤 Standard User"

        user_data["balance"] += reward
        user_data["lootboxes"] += boxes_found
        user_data["streak"] = streak + 1
        user_data["last_daily"] = now.isoformat()
        save_json(DB_FILE, data)

        # Create Embed
        embed = discord.Embed(
            title="✨ GLOBAL DAILY REWARD ✨", 
            description=f"Congratulations {ctx.author.mention}!\nStatus: `{status_text}`", 
            color=0xF1C40F if user_is_premium else 0x2ecc71
        )
        embed.add_field(name="💰 Coins Found", value=f"**{reward:,}** Coins", inline=True)
        embed.add_field(name="🎁 Lootboxes", value=f"**{boxes_found}** Boxes 📦", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{user_data['streak']}** Days", inline=False)
        embed.add_field(name="🎒 Total Lootboxes", value=f"**{user_data['lootboxes']}**", inline=True)

        img_url = config.get('image_url', "https://cdn.discordapp.com/attachments/1439489026225868892/1470689376060313683/daily-22-15001.gif")
        embed.set_image(url=img_url)
        
        embed.set_footer(text=f"Global Economy • Total Balance: {user_data['balance']:,}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DailyCommand(bot))
