import discord
from discord.ui import View, Button, Modal, TextInput
import json
import os
import datetime

# ==========================================
# CONFIGURATION & DATABASE
# ==========================================

CONFIG_FILE = 'config.json'
OWNER_ID = 1311355680640208926  # আপনার Discord ID

# প্রিমিয়াম প্রাইস (এডিট করতে পারেন)
PRICES = {
    "user": "50 Taka/Month",
    "server": "100 Taka/Month"
}

def load_config():
    """
    পুরনো এবং নতুন সব ডাটা লোড করবে।
    পুরনো ফিচার (Anti-link, Welcome) নষ্ট হবে না।
    """
    default_data = {
        # --- LEGACY FEATURES (আপনার আগের লজিক) ---
        "anti_link": {"enabled": False, "blocked_list": [], "bypass_roles": [], "blocked_keywords": []},
        "bad_words": [],
        "auto_role_id": None,
        "welcome": {"enabled": True, "channel_id": None, "title": "Welcome!", "description": "Hi {member}!", "image_url": None, "color": 0x00ff00},
        "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "image_url": None, "color": 0xff0000},
        
        # --- NEW PREMIUM DATA ---
        "premium_users": {},
        "premium_servers": {}
    }

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # যদি কোনো কি (Key) মিসিং থাকে, ডিফল্ট থেকে নিয়ে নেবে
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
# CORE LOGIC: COLOR & CHECKER
# ==========================================

def get_theme_color(user_id, guild_id=None):
    """
    এই ফাংশনটি চেক করবে ইউজার বা সার্ভার প্রিমিয়াম কিনা।
    প্রিমিয়াম হলে Gold কালার দেবে, না হলে Blue কালার দেবে।
    """
    config = load_config()
    now = datetime.datetime.now()
    
    # ১. ইউজার প্রিমিয়াম চেক
    if str(user_id) in config.get("premium_users", {}):
        expiry = datetime.datetime.fromisoformat(config["premium_users"][str(user_id)]["expiry"])
        if now < expiry:
            return discord.Color.gold() # 🟡 Premium User

    # ২. সার্ভার প্রিমিয়াম চেক
    if guild_id and str(guild_id) in config.get("premium_servers", {}):
        expiry = datetime.datetime.fromisoformat(config["premium_servers"][str(guild_id)]["expiry"])
        if now < expiry:
            return discord.Color.gold() # 🟡 Premium Server

    # ৩. প্রিমিয়াম না থাকলে ব্লু
    return discord.Color.blue() # 🔵 Free User

def activate_premium(target_id, p_type, days=30):
    """প্রিমিয়াম অ্যাক্টিভ করার সিম্পল ফাংশন"""
    config = load_config()
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    data = {
        "active": True,
        "expiry": expiry.isoformat(),
        "type": p_type
    }
    
    if p_type == "user":
        config["premium_users"][str(target_id)] = data
    elif p_type == "server":
        config["premium_servers"][str(target_id)] = data
        
    save_config(config)

# ==========================================
# UI VIEWS & MODALS
# ==========================================

# ১. পেমেন্ট ইনফো নেওয়ার মডাল
class PaymentModal(Modal):
    def __init__(self, p_type):
        super().__init__(title=f"Buy {p_type.title()} Premium")
        self.p_type = p_type
        
        self.trx_id = TextInput(label="Transaction ID (TrxID)", placeholder="Example: 8G7D...", required=True)
        self.method = TextInput(label="Payment Method", placeholder="bKash / Nagad", required=True)
        self.add_item(self.trx_id)
        self.add_item(self.method)

    async def on_submit(self, interaction: discord.Interaction):
        # ইউজারকে কনফার্মেশন
        await interaction.response.send_message("✅ Payment details sent to Admin! Please wait for approval.", ephemeral=True)
        
        # অ্যাডমিনকে নোটিফিকেশন
        owner = interaction.client.get_user(OWNER_ID)
        if owner:
            target_id = interaction.user.id if self.p_type == "user" else interaction.guild.id
            
            embed = discord.Embed(title="💸 New Premium Request", color=discord.Color.gold())
            embed.add_field(name="Buyer", value=f"{interaction.user} ({interaction.user.id})", inline=False)
            embed.add_field(name="Type", value=self.p_type.upper(), inline=True)
            embed.add_field(name="Target ID", value=f"`{target_id}`", inline=True)
            embed.add_field(name="TrxID", value=f"`{self.trx_id.value}`", inline=False)
            embed.add_field(name="Method", value=f"`{self.method.value}`", inline=False)
            
            await owner.send(embed=embed, view=AdminApprovalView(target_id, self.p_type))

# ২. অ্যাডমিন অ্যাপ্রুভাল বাটন
class AdminApprovalView(View):
    def __init__(self, target_id, p_type):
        super().__init__(timeout=None)
        self.target_id = target_id
        self.p_type = p_type

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: Button):
        activate_premium(self.target_id, self.p_type)
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
        
