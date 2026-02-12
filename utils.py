import discord
from discord.ui import View, Button, Modal, TextInput
import json
import os
import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================

CONFIG_FILE = 'config.json'
OWNER_ID = 1311355680640208926  # আপনার Discord ID

# শুধু সার্ভার প্রাইস থাকবে
PREMIUM_PRICE = "100 Taka/Month"

def load_config():
    """ডাটাবেস লোড করা (Legacy Support সহ)"""
    default_data = {
        # --- LEGACY FEATURES (আপনার আগের লজিক) ---
        "anti_link": {"enabled": False, "blocked_list": [], "bypass_roles": [], "blocked_keywords": []},
        "bad_words": [],
        "auto_role_id": None,
        "welcome": {"enabled": True, "channel_id": None, "title": "Welcome!", "description": "Hi {member}!", "image_url": None, "color": 0x00ff00},
        "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "image_url": None, "color": 0xff0000},
        
        # --- ONLY SERVER PREMIUM ---
        "premium_servers": {},
        # (user premium সেকশন বাদ দেওয়া হলো)
        "giveaway_settings": {} 
    }

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            for key, value in default_data.items():
                if key not in data:
                    data[key] = value
            return data
        except:
            return default_data

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# ==========================================
# 2. CORE LOGIC: ONLY SERVER CHECK
# ==========================================

def get_theme_color(guild_id):
    """
    শুধুমাত্র সার্ভার আইডি চেক করবে।
    Premium Server = Gold (🟡)
    Free Server = Blue (🔵)
    """
    if not guild_id: return discord.Color.blue()
    
    config = load_config()
    now = datetime.datetime.now()
    
    # সার্ভার প্রিমিয়াম চেক
    if str(guild_id) in config.get("premium_servers", {}):
        expiry_str = config["premium_servers"][str(guild_id)]["expiry"]
        try:
            expiry = datetime.datetime.fromisoformat(expiry_str)
            if now < expiry:
                return discord.Color.gold() # 🟡 Premium
        except:
            pass # ডেট এরর হলে ইগনোর করবে

    return discord.Color.blue() # 🔵 Free

def activate_server_premium(guild_id, days=30):
    """সার্ভার প্রিমিয়াম অ্যাক্টিভ করা"""
    config = load_config()
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    data = {
        "active": True,
        "expiry": expiry.isoformat()
    }
    
    config["premium_servers"][str(guild_id)] = data
    save_config(config)

# ==========================================
# 3. UI VIEWS (Only Server Options)
# ==========================================

class PaymentModal(Modal, title="Buy Server Premium"):
    def __init__(self):
        super().__init__()
        self.trx_id = TextInput(label="Transaction ID (TrxID)", placeholder="Example: 8G7D...", required=True)
        self.method = TextInput(label="Payment Method", placeholder="bKash / Nagad / Rocket", required=True)
        self.add_item(self.trx_id)
        self.add_item(self.method)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ পেমেন্ট ডিটেইলস অ্যাডমিনের কাছে পাঠানো হয়েছে।", ephemeral=True)
        
        owner = interaction.client.get_user(OWNER_ID)
        if owner:
            embed = discord.Embed(title="🏰 New Server Premium Request", color=discord.Color.gold())
            embed.add_field(name="Buyer", value=f"{interaction.user} ({interaction.user.id})", inline=False)
            embed.add_field(name="Server ID", value=f"`{interaction.guild.id}`", inline=True)
            embed.add_field(name="Server Name", value=f"`{interaction.guild.name}`", inline=True)
            embed.add_field(name="TrxID", value=f"`{self.trx_id.value}`", inline=False)
            embed.add_field(name="Method", value=f"`{self.method.value}`", inline=False)
            
            await owner.send(embed=embed, view=AdminApprovalView(interaction.guild.id))

class AdminApprovalView(View):
    def __init__(self, target_id):
        super().__init__(timeout=None)
        self.target_id = target_id

    @discord.ui.button(label="✅ Approve Server", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: Button):
        activate_server_premium(self.target_id)
        await interaction.response.send_message(f"✅ Server Premium Activated! (ID: `{self.target_id}`)")
        self.stop()

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ Request Rejected.")
        self.stop()

class PremiumSelectionView(View):
    @discord.ui.button(label="🏰 Buy Server Premium", style=discord.ButtonStyle.success, emoji="👑")
    async def buy_server(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PaymentModal())
        await interaction.response.send_message(f"✅ **{self.p_type.upper()} Premium** Activated for ID: `{self.target_id}`")
        self.stop()

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"❌ Request Rejected.")
        self.stop()

# ৩. ইউজার যখন কমান্ড দেবে তখন এই বাটন আসবে
class PremiumSelectionView(View):
    @discord.ui.button(label="👤 Buy User Premium", style=discord.ButtonStyle.primary, emoji="👤")
    async def buy_user(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PaymentModal("user"))

    @discord.ui.button(label="🏰 Buy Server Premium", style=discord.ButtonStyle.success, emoji="🏰")
    async def buy_server(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PaymentModal("server"))
        
