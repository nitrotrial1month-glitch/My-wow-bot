import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View
import json
import os
import datetime
import random
from utils import check_advanced_premium 

# ফাইল পাথ
DB_FILE = 'economy.json'
CONFIG_FILE = 'daily_config.json'

# --- JSON লোড/সেভ ফাংশন ---
def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ==========================================
# 1. PERSONAL DASHBOARD (Custom Image Setter)
# ==========================================
class PersonalCustomizeModal(Modal, title="🎨 Customize Your Daily"):
    img_input = TextInput(
        label="Custom GIF/Image URL", 
        placeholder="https://media.giphy.com/...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # ইউজারের দেওয়া লিঙ্ক ডাটাবেসে সেভ করা হবে
        data = load_json(DB_FILE)
        uid = str(interaction.user.id)
        
        if uid not in data:
            data[uid] = {"balance": 0, "streak": 0, "last_daily": None, "lootboxes": 0}
            
        # কাস্টম ইমেজ সেভ করা
        data[uid]["custom_image"] = self.img_input.value
        save_json(DB_FILE, data)
        
        await interaction.response.send_message("✅ **Success!** Your personal Daily image has been set.", ephemeral=True)

# ==========================================
# 2. VIEW WITH BUTTONS
# ==========================================
class DailyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    # 🎨 কাস্টমাইজ বাটন (শুধুমাত্র প্রিমিয়াম ইউজারদের জন্য)
    @discord.ui.button(label="Customize Look", style=discord.ButtonStyle.secondary, emoji="🎨", custom_id="daily_custom_btn")
    async def customize_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # প্রিমিয়াম চেক
        status = check_advanced_premium(interaction.user.id)
        
        if not status["active"]:
            return await interaction.response.send_message(
                "🔒 **Premium Feature!**\nOnly Premium members can set a custom GIF for their daily command.\nUse `/buy_premium` to unlock.", 
                ephemeral=True
            )
        
        # মডাল ওপেন করা
        await interaction.response.send_modal(PersonalCustomizeModal())

# ==========================================
# 3. MAIN COMMAND
# ==========================================
class DailyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="daily", description="Claim daily rewards & lootboxes!")
    async def daily(self, ctx: commands.Context):
        data = load_json(DB_FILE)
        config = load_json(CONFIG_FILE) # গ্লোবাল কনফিগ (ডিফল্ট ছবির জন্য)
        
        user_id = str(ctx.author.id)
        now = datetime.datetime.now(datetime.timezone.utc)

        # ডাটা তৈরি (যদি না থাকে)
        if user_id not in data:
            data[user_id] = {"balance": 0, "streak": 0, "last_daily": None, "lootboxes": 0}
        
        user_data = data[user_id]
        
        # --- Cooldown Check ---
        last_daily_str = user_data.get("last_daily")
        if last_daily_str:
            last_daily = datetime.datetime.fromisoformat(last_daily_str)
            if (now.timestamp() - last_daily.timestamp()) < 86400:
                time_left = datetime.timedelta(seconds=86400 - (now.timestamp() - last_daily.timestamp()))
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return await ctx.send(f"⏳ Please wait **{hours}h {minutes}m**!", ephemeral=True)

        # --- Premium Logic (Multipliers) ---
        status = check_advanced_premium(ctx.author.id)
        
        streak = user_data.get("streak", 0)
        base_reward = 500 + (streak * 50)
        
        multiplier = 1.0
        tier_name = "Free"
        boxes = random.randint(1, 2)
        color = 0x2ecc71 # Green

        if status["active"]:
            tier = status["tier"]
            if tier == "basic":
                multiplier = 2.0
                tier_name = "🥉 Basic"
                color = 0xe67e22
            elif tier == "pro":
                multiplier = 3.0
                tier_name = "🥈 Pro"
                color = 0x3498db
            elif tier == "ultra":
                multiplier = 4.0
                boxes = random.randint(5, 10)
                tier_name = "🥇 Ultra"
                color = 0xF1C40F

        final_reward = int(base_reward * multiplier)
        
        # ডাটা আপডেট
        user_data["balance"] += final_reward
        user_data["lootboxes"] += boxes
        user_data["streak"] += 1
        user_data["last_daily"] = now.isoformat()
        
        save_json(DB_FILE, data)

        # --- IMAGE LOGIC (Personal vs Global) ---
        # ১. ডিফল্ট ইমেজ (অ্যাডমিন যেটা সেট করেছে)
        final_image = config.get('image_url', "https://cdn.discordapp.com/attachments/1439489026225868892/1470689376060313683/daily-22-15001.gif")
        
        # ২. যদি প্রিমিয়াম ইউজারের পার্সোনাল ইমেজ থাকে, তবে সেটা নিবে
        if status["active"] and "custom_image" in user_data:
            if user_data["custom_image"]: # যদি খালি না হয়
                final_image = user_data["custom_image"]

        # --- Embed ---
        embed = discord.Embed(
            title="✨ DAILY CLAIMED ✨", 
            description=f"User: {ctx.author.mention}\nTier: **{tier_name}** ({int(multiplier)}x Boost)", 
            color=color
        )
        embed.add_field(name="💰 Received", value=f"**{final_reward:,}** Coins", inline=True)
        embed.add_field(name="📦 Lootboxes", value=f"**+{boxes}** New", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{user_data['streak']}** Days", inline=True)
        
        embed.set_image(url=final_image)
        embed.set_footer(text=f"Total: {user_data['balance']:,} coins")
        
        # বাটনসহ পাঠানো
        await ctx.send(embed=embed, view=DailyView())

async def setup(bot):
    await bot.add_cog(DailyCommand(bot))
    
