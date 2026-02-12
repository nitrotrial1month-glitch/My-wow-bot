import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import json
import os
import datetime

# ==========================================
# PART 1: LEGACY CODE (আপনার দেওয়া কোড - অপরিবর্তিত)
# ==========================================

CONFIG_FILE = 'config.json'
PREFIX_FILE = 'prefixes.json' # প্রিফিক্স ফাইল নাম যদি লাগে

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_data = {
            "anti_link": {"enabled": False, "blocked_list": [], "bypass_roles": [], "blocked_keywords": []},
            "bad_words": [],
            "auto_role_id": None,
            "welcome": {"enabled": True, "channel_id": None, "title": "Welcome!", "description": "Hi {member}!", "image_url": None, "color": 0x00ff00},
            "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "image_url": None, "color": 0xff0000},
            "premium": {} 
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try: 
            data = json.load(f)
            # নিশ্চিত করা হচ্ছে যেন 'premium' কি-টি সব সময় থাকে
            if "premium" not in data:
                data["premium"] = {}
            return data
        except: 
            return {"premium": {}} # এরর হলেও যেন প্রিমিয়াম চেক না আটকায়

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def is_user_premium(user_id):
    """এটি আপনার পুরনো কমান্ডগুলোর জন্য রাখা হয়েছে"""
    config = load_config()
    premium_data = config.get("premium", {})
    user_id_str = str(user_id) # আইডি স্ট্রিং হিসেবে চেক করা নিরাপদ
    
    if user_id_str in premium_data:
        try:
            expiry_date_str = premium_data[user_id_str]
            expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
            
            if datetime.datetime.now() < expiry_date:
                return True
            else:
                # মেয়াদ শেষ হলে অটো ডিলিট
                del config["premium"][user_id_str]
                save_config(config)
                return False
        except Exception:
            return False
    return False

def add_premium(user_id, days):
    """পুরনো সিস্টেমে প্রিমিয়াম অ্যাড করা"""
    config = load_config()
    if "premium" not in config: config["premium"] = {}
    
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
    config["premium"][str(user_id)] = expiry_date.isoformat()
    save_config(config)
    return expiry_date

# ==========================================
# PART 2: NEW ADVANCED SYSTEM (নতুন লজিক)
# ==========================================

OWNER_ID = 1311355680640208926  # আপনার Discord ID

# টিয়ার এবং প্রাইস লিস্ট
TIER_INFO = {
    "basic": {"price": "50", "limit": 100, "days": 30},
    "pro":   {"price": "100", "limit": 500, "days": 30},
    "ultra": {"price": "200", "limit": 999999, "days": 30}
}

def activate_advanced_premium(target_id, p_type, tier):
    """
    নতুন ডাটাবেস স্ট্রাকচার ব্যবহার করে প্রিমিয়াম অ্যাড করা।
    এটি পুরনো 'premium' key ব্যবহার না করে নতুন key ব্যবহার করবে।
    """
    config = load_config()
    
    # নতুন সেকশন না থাকলে বানিয়ে নেবে (সেফটি)
    if "premium_users" not in config: config["premium_users"] = {}
    if "premium_servers" not in config: config["premium_servers"] = {}
    
    days = TIER_INFO[tier]["days"]
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    new_data = {
        "tier": tier,
        "expiry": expiry.isoformat(),
        "limit": TIER_INFO[tier]["limit"]
    }
    
    # সঠিক জায়গায় সেভ করা
    if p_type == "user":
        config["premium_users"][str(target_id)] = new_data
    else:
        config["premium_servers"][str(target_id)] = new_data
        
    save_config(config)
    return expiry

def check_advanced_premium(user_id, guild_id=None):
    """
    এটি নতুন এবং পুরনো—উভয় সিস্টেম চেক করবে।
    """
    config = load_config()
    now = datetime.datetime.now()
    
    # ১. নতুন ইউজার প্রিমিয়াম চেক
    if "premium_users" in config and str(user_id) in config["premium_users"]:
        data = config["premium_users"][str(user_id)]
        if now < datetime.datetime.fromisoformat(data["expiry"]):
            return {"active": True, "tier": data["tier"], "type": "user"}

    # ২. নতুন সার্ভার প্রিমিয়াম চেক
    if guild_id and "premium_servers" in config and str(guild_id) in config["premium_servers"]:
        data = config["premium_servers"][str(guild_id)]
        if now < datetime.datetime.fromisoformat(data["expiry"]):
            return {"active": True, "tier": data["tier"], "type": "server"}
            
    # ৩. পুরনো সিস্টেম চেক (Fallback)
    if is_user_premium(user_id):
        return {"active": True, "tier": "legacy", "type": "user"}

    return {"active": False}

# --- ADMIN ACTION VIEW (Accept / Reject) ---
class AdminActionView(View):
    def __init__(self, target_id, buyer_id, p_type, tier):
        super().__init__(timeout=None)
        self.target_id = target_id
        self.buyer_id = buyer_id
        self.p_type = p_type
        self.tier = tier

    @discord.ui.button(label="✅ Accept & Activate", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        # নতুন ফাংশন ব্যবহার করে ডাটা সেভ
        expiry = activate_advanced_premium(self.target_id, self.p_type, self.tier)
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="Status", value="✅ **APPROVED**", inline=False)
        embed.add_field(name="Expiry", value=f"`{expiry.strftime('%Y-%m-%d')}`", inline=True)
        
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        
        try:
            buyer = await interaction.client.fetch_user(self.buyer_id)
            await buyer.send(f"🎉 **Premium Active!** Tier: {self.tier.upper()} | Type: {self.p_type}")
        except: pass

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Status", value="❌ **REJECTED**", inline=False)
        
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

        try:
            buyer = await interaction.client.fetch_user(self.buyer_id)
            await buyer.send(f"❌ Your premium request for **{self.tier.upper()}** was declined.")
        except: pass

# --- PAYMENT MODAL ---
class PaymentModal(Modal):
    def __init__(self, p_type, tier, target_id):
        price = TIER_INFO[tier]["price"]
        super().__init__(title=f"Pay {price} BDT")
        self.p_type = p_type
        self.tier = tier
        self.target_id = target_id
        
        self.tx_input = TextInput(label="Transaction ID (TxID)", placeholder="Enter TrxID...", min_length=5, required=True)
        self.add_item(self.tx_input)

    async def on_submit(self, interaction: discord.Interaction):
        owner = interaction.client.get_user(OWNER_ID)
        
        embed = discord.Embed(title="💰 New Premium Order", color=discord.Color.gold())
        embed.add_field(name="Buyer", value=f"{interaction.user.mention} (`{interaction.user.id}`)")
        embed.add_field(name="Type", value=f"**{self.p_type.upper()}** | {self.tier.upper()}")
        embed.add_field(name="Target ID", value=f"`{self.target_id}`")
        embed.add_field(name="TxID", value=f"```{self.tx_input.value}```")
        
        view = AdminActionView(self.target_id, interaction.user.id, self.p_type, self.tier)
        await owner.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Check DM for updates!", ephemeral=True)

# --- TIER SELECT VIEW ---
class TierSelectView(View):
    def __init__(self, p_type, target_id):
        super().__init__()
        self.p_type = p_type
        self.target_id = target_id

    @discord.ui.button(label="Basic (50₹)", style=discord.ButtonStyle.secondary)
    async def basic(self, interaction, button):
        await interaction.response.send_modal(PaymentModal(self.p_type, "basic", self.target_id))

    @discord.ui.button(label="Pro (100₹)", style=discord.ButtonStyle.primary)
    async def pro(self, interaction, button):
        await interaction.response.send_modal(PaymentModal(self.p_type, "pro", self.target_id))
    
    @discord.ui.button(label="Ultra (200₹)", style=discord.ButtonStyle.danger)
    async def ultra(self, interaction, button):
        await interaction.response.send_modal(PaymentModal(self.p_type, "ultra", self.target_id))

# --- MAIN PREMIUM VIEW ---
class PremiumTypeView(View):
    @discord.ui.button(label="For ME (User)", style=discord.ButtonStyle.blurple, emoji="👤")
    async def for_user(self, interaction, button):
        await interaction.response.send_message("Select Tier:", view=TierSelectView("user", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="For SERVER", style=discord.ButtonStyle.green, emoji="🏰")
    async def for_server(self, interaction, button):
        await interaction.response.send_message("Select Tier:", view=TierSelectView("server", interaction.guild.id), ephemeral=True)
                
