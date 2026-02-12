import discord
from discord.ui import View, Button, Modal, TextInput
import json
import os
import datetime

# --- কনফিগারেশন ---
CONFIG_FILE = 'config.json'
OWNER_ID = 1311355680640208926  # আপনার আইডি বসান
PRICES = {"user": "50 Taka/Month", "server": "100 Taka/Month"}

# --- ১. ডাটাবেস লোড ও সেভ ---
def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, 'r') as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- ২. প্রিমিয়াম অ্যাক্টিভ করা ---
def activate_premium(target_id, p_type, days=30):
    config = load_config()
    if "premium_users" not in config: config["premium_users"] = {}
    if "premium_servers" not in config: config["premium_servers"] = {}
    
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    data = {"active": True, "expiry": expiry.isoformat(), "type": p_type}
    
    if p_type == "user": config["premium_users"][str(target_id)] = data
    else: config["premium_servers"][str(target_id)] = data
    save_config(config)

# --- ৩. কালার লজিক (গোল্ড বা ব্লু) ---
def get_theme_color(user_id, guild_id=None):
    config = load_config()
    now = datetime.datetime.now()
    
    # ইউজার চেক
    if str(user_id) in config.get("premium_users", {}):
        if now < datetime.datetime.fromisoformat(config["premium_users"][str(user_id)]["expiry"]):
            return discord.Color.gold()

    # সার্ভার চেক
    if guild_id and str(guild_id) in config.get("premium_servers", {}):
        if now < datetime.datetime.fromisoformat(config["premium_servers"][str(guild_id)]["expiry"]):
            return discord.Color.gold()

    return discord.Color.blue() # ডিফল্ট কালার

# --- ৪. পেমেন্ট মডাল (ইংলিশ ইন্টারফেস, বাংলা রিপ্লাই) ---
class PaymentModal(Modal):
    def __init__(self, p_type):
        super().__init__(title=f"Buy {p_type.title()} Premium") # ইংলিশ টাইটেল
        self.p_type = p_type
        
        # ইংলিশ লেবেল
        self.trx_id = TextInput(label="Transaction ID (TrxID)", placeholder="Example: 8G7D...", required=True)
        self.method = TextInput(label="Payment Method", placeholder="bKash / Nagad", required=True)
        self.add_item(self.trx_id)
        self.add_item(self.method)

    async def on_submit(self, interaction: discord.Interaction):
        # ইউজারের কাছে মেসেজ (বাংলায়)
        await interaction.response.send_message("✅ আপনার পেমেন্ট রিকোয়েস্টটি অ্যাডমিনের কাছে পাঠানো হয়েছে! শীঘ্রই কনফার্ম করা হবে।", ephemeral=True)
        
        # অ্যাডমিনের কাছে মেসেজ (ইংলিশে, যাতে বুঝতে সুবিধা হয়)
        owner = interaction.client.get_user(OWNER_ID)
        if owner:
            embed = discord.Embed(title="💸 New Premium Request", color=discord.Color.gold())
            embed.add_field(name="Buyer", value=f"{interaction.user}", inline=False)
            embed.add_field(name="Type", value=self.p_type.upper(), inline=True)
            embed.add_field(name="Method", value=self.method.value, inline=True)
            embed.add_field(name="TrxID", value=self.trx_id.value, inline=False)
            
            # টার্গেট আইডি (ইউজার নাকি সার্ভার)
            target = interaction.user.id if self.p_type == "user" else interaction.guild.id
            await owner.send(embed=embed, view=AdminApprovalView(target, self.p_type))

# --- ৫. অ্যাডমিন অ্যাপ্রুভাল ---
class AdminApprovalView(View):
    def __init__(self, target_id, p_type):
        super().__init__(timeout=None)
        self.target_id = target_id
        self.p_type = p_type

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: Button):
        activate_premium(self.target_id, self.p_type)
        await interaction.response.send_message(f"✅ সফলভাবে **{self.p_type} Premium** চালু করা হয়েছে! (ID: {self.target_id})")
        self.stop()

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"❌ রিকোয়েস্টটি বাতিল করা হয়েছে।")
        self.stop()

# --- ৬. সিলেকশন ভিউ (ইংলিশ বাটন) ---
class PremiumSelectionView(View):
    @discord.ui.button(label="👤 Buy User Premium", style=discord.ButtonStyle.primary)
    async def buy_user(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PaymentModal("user"))

    @discord.ui.button(label="🏰 Buy Server Premium", style=discord.ButtonStyle.success)
    async def buy_server(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PaymentModal("server"))
                                                
