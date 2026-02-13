import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View
import json
import os
import datetime
import random
# utils থেকে ইমপোর্ট করা হচ্ছে
from utils import load_config, save_config, get_theme_color

DB_FILE = 'economy.json'

# --- JSON Helpers ---
def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ==========================================
# 1. PREMIUM DASHBOARD MODAL
# ==========================================
class DailyDashboardModal(Modal, title="💎 Premium Daily Dashboard"):
    def __init__(self):
        super().__init__()
        config = load_config()
        d_set = config.get("daily_settings", {})
        
        self.img_input = TextInput(
            label="Custom GIF/Image URL", 
            default=d_set.get("image_url", ""),
            placeholder="https://media.giphy.com/...",
            required=False
        )
        self.msg_input = TextInput(
            label="Custom Daily Message", 
            default=d_set.get("message", "Enjoy your daily rewards!"),
            style=discord.TextStyle.paragraph,
            required=False
        )
        self.add_item(self.img_input)
        self.add_item(self.msg_input)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        config["daily_settings"] = {
            "image_url": self.img_input.value,
            "message": self.msg_input.value
        }
        save_config(config)
        await interaction.response.send_message("✅ **Daily Dashboard Updated Successfully!**", ephemeral=True)

# ==========================================
# 2. MAIN COG (Hybrid Commands)
# ==========================================
class DailyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium(self, guild_id):
        """সার্ভার প্রিমিয়াম কি না চেক করবে"""
        if not guild_id: return False
        return get_theme_color(guild_id) == discord.Color.gold()

    # --- 💎 Dashboard Command (Hybrid) ---
    @commands.hybrid_command(name="daily_dashboard", description="💎 [PREMIUM] Configure custom image and message")
    @app_commands.checks.has_permissions(administrator=True)
    async def daily_dashboard(self, ctx: commands.Context):
        if not self.is_premium(ctx.guild.id):
            embed = discord.Embed(
                title="🔒 Feature Locked",
                description="Customizing the daily system is restricted to **Premium Servers**.\n\n⭐ Unlock now with `/buy_premium`.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)
        
        # হাইব্রিড কমান্ডে সরাসরি মডাল পাঠানো যায় না, তাই শুধু স্ল্যাশ কমান্ডের ক্ষেত্রে এটি কাজ করবে
        if ctx.interaction:
            await ctx.interaction.response.send_modal(DailyDashboardModal())
        else:
            await ctx.send("❌ Please use the Slash Command `/daily_dashboard` to open the settings modal.", delete_after=10)

    # --- 💰 Main Daily Command (Hybrid) ---
    @commands.hybrid_command(name="daily", description="Claim your daily coins and rewards")
    async def daily(self, ctx: commands.Context):
        data = load_db()
        config = load_config()
        user_id = str(ctx.author.id)
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # প্রিমিয়াম স্ট্যাটাস চেক
        is_prem = self.is_premium(ctx.guild.id)
        color = get_theme_color(ctx.guild.id)
        
        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None, "lootboxes": 0}
        
        user_data = data[user_id]
        
        # Cooldown Check (24 Hours)
        last_daily_str = user_data.get("last_daily")
        if last_daily_str:
            last_daily = datetime.datetime.fromisoformat(last_daily_str)
            if (now.timestamp() - last_daily.timestamp()) < 86400:
                time_left = datetime.timedelta(seconds=86400 - (now.timestamp() - last_daily.timestamp()))
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return await ctx.send(f"⏳ Please wait **{hours}h {minutes}m** before claiming again!", ephemeral=True)

        # Reward Calculation
        streak = user_data.get("streak", 0)
        multiplier = 2.0 if is_prem else 1.0 # প্রিমিয়ামে ২ গুণ রিওয়ার্ড
        base_reward = (500 + (streak * 50)) * multiplier
        
        boxes = random.randint(5, 10) if is_prem else random.randint(1, 2)
        final_reward = int(base_reward)
        
        # Update DB
        user_data["balance"] += final_reward
        user_data["lootboxes"] += boxes
        user_data["streak"] += 1
        user_data["last_daily"] = now.isoformat()
        save_db(data)

        # Design (Falcon/Nova Style)
        d_set = config.get("daily_settings", {})
        custom_msg = d_set.get("message", "Enjoy your daily rewards!")
        
        embed = discord.Embed(
            title="✨ DAILY REWARD CLAIMED ✨",
            description=(
                f"### {custom_msg}\n"
                f"────────────────────\n"
                f"• **Coins Received:** {final_reward:,} 💰\n"
                f"• **Lootboxes:** +{boxes} 📦\n"
                f"• **Current Streak:** {user_data['streak']} Days 🔥\n"
                f"────────────────────"
            ),
            color=color
        )
        
        # ইমেজ সেট করা
        final_img = d_set.get("image_url") if is_prem and d_set.get("image_url") else "https://cdn.discordapp.com/attachments/1439489026225868892/1470689376060313683/daily-22-15001.gif"
        embed.set_image(url=final_img)
        embed.set_footer(text=f"Total Balance: {user_data['balance']:,} coins | {ctx.author.name}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DailyCommand(bot))
