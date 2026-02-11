import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import os
import datetime
import random # লুটবক্সের সংখ্যার জন্য র‍্যান্ডম ইমপোর্ট করা হয়েছে

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

# --- Dashboard Modal ---
class DailyDashboardModal(Modal, title="Daily Command Dashboard"):
    img_input = TextInput(label="Main Image/GIF URL", required=False)
    thumb_input = TextInput(label="Thumbnail URL (Optional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_json(CONFIG_FILE)
        config['image_url'] = self.img_input.value if self.img_input.value else "https://cdn.discordapp.com/attachments/1439489026225868892/1470689376060313683/daily-22-15001.gif?ex=698c35b7&is=698ae437&hm=14b2a92af8b6cd0c084854b564dd4e30bd1631a7110c3ef13312d2b2fd815b08&"
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

        # ইউজার ডেটা চেক এবং ডিফল্ট ভ্যালু (lootboxes যুক্ত করা হয়েছে)
        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None, "lootboxes": 0}
        
        user_data = data[user_id]
        if "lootboxes" not in user_data: # পুরোনো ইউজারদের জন্য চেক
            user_data["lootboxes"] = 0

        last_daily_str = user_data.get("last_daily")
        
        # Cooldown check
        if last_daily_str:
            last_daily = datetime.datetime.fromisoformat(last_daily_str)
            if (now - last_daily).total_seconds() < 86400:
                time_left = datetime.timedelta(seconds=86400 - (now - last_daily).total_seconds())
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return await ctx.send(f"⏳ Please wait **{hours}h {minutes}m** before claiming your rewards again!", ephemeral=True)

        # Reward Calculation (Coins)
        streak = user_data.get("streak", 0)
        reward = 800 + (streak * 200)
        user_data["balance"] += reward
        
        # --- Lootbox Logic (1 to 3 boxes) ---
        boxes_found = random.randint(1, 3)
        user_data["lootboxes"] += boxes_found
        
        # Streak and Time update
        user_data["streak"] = streak + 1
        user_data["last_daily"] = now.isoformat()
        save_json(DB_FILE, data)

        # Create Embed
        embed = discord.Embed(
            title="✨ GLOBAL DAILY REWARD ✨", 
            description=f"Congratulations {ctx.author.mention}, you've claimed your rewards!", 
            color=0x2ecc71
        )
        embed.add_field(name="💰 Coins Found", value=f"**{reward:,}** Coins", inline=True)
        embed.add_field(name="🎁 Lootboxes", value=f"**{boxes_found}** Boxes 📦", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{user_data['streak']}** Days", inline=False)
        
        # Total Stats in Footer or Field
        embed.add_field(name="🎒 Your Total Lootboxes", value=f"**{user_data['lootboxes']}**", inline=True)

        img_url = config.get('image_url', "https://cdn.discordapp.com/attachments/1439489026225868892/1470689376060313683/daily-22-15001.gif?ex=698c35b7&is=698ae437&hm=14b2a92af8b6cd0c084854b564dd4e30bd1631a7110c3ef13312d2b2fd815b08&")
        embed.set_image(url=img_url)
        
        if config.get('thumb_url'):
            embed.set_thumbnail(url=config['thumb_url'])
        
        embed.set_footer(text=f"Global Economy • Total Balance: {user_data['balance']:,}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DailyCommand(bot))
    
