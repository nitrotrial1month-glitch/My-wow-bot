import discord
from discord.ext import commands
from discord import app_commands
import datetime
from utils import load_config, save_config 

# আপনার ডিসকোর্ড আইডি
OWNER_ID = 1311355680640208926 

# --- ১. পেমেন্ট ফর্ম (Modal) ---
class PaymentModal(discord.ui.Modal):
    def __init__(self, days):
        # টাইটেল এবং custom_id একদম ছোট রাখা হয়েছে যাতে এরর না আসে
        super().__init__(title="Submit Payment", custom_id=f"pay_{days}")
        self.days = days
        
        self.tx_id = discord.ui.TextInput(
            label="Transaction ID (TxID)",
            placeholder="Enter TxnID here...",
            min_length=5,
            max_length=25, # দৈর্ঘ্য সীমিত করা হলো
            required=True,
            custom_id="txn_field"
        )

    async def on_submit(self, interaction: discord.Interaction):
        owner = interaction.client.get_user(OWNER_ID)
        if not owner:
            return await interaction.response.send_message("Error: Owner offline.", ephemeral=True)
            
        embed = discord.Embed(title="New Premium Request", color=discord.Color.blue())
        embed.add_field(name="User", value=f"{interaction.user.mention} (`{interaction.user.id}`)")
        embed.add_field(name="Plan", value=f"{self.days} Days")
        embed.add_field(name="TxnID", value=f"`{self.tx_id.value}`")
        
        # ওনারের কাছে পাঠানো
        view = AdminConfirmView(interaction.user.id, self.days)
        await owner.send(embed=embed, view=view)
        
        await interaction.response.send_message("✅ Request sent! Please wait.", ephemeral=True)

# --- ২. ওনার কনফার্মেশন বাটন ---
class AdminConfirmView(discord.ui.View):
    def __init__(self, user_id, days):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.days = days

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="adm_app")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()
        if "premium" not in config: config["premium"] = {}
        
        expiry = datetime.datetime.now() + datetime.timedelta(days=self.days)
        config["premium"][str(self.user_id)] = expiry.isoformat()
        save_config(config)
        
        await interaction.response.edit_message(content=f"✅ Activated for <@{self.user_id}>", view=None)

# --- ৩. মেইন বাই বাটন ভিউ ---
class PremiumBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # টাইমআউট বন্ধ রাখা হলো

    @discord.ui.button(label="30 Days - 49 BDT", style=discord.ButtonStyle.primary, emoji="⭐", custom_id="buy_30")
    async def buy_30(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(30))

    @discord.ui.button(label="90 Days - 129 BDT", style=discord.ButtonStyle.primary, emoji="🌟", custom_id="buy_90")
    async def buy_90(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(90))

    @discord.ui.button(label="365 Days - 399 BDT", style=discord.ButtonStyle.primary, emoji="👑", custom_id="buy_365")
    async def buy_365(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(365))

# --- ৪. কগ ক্লাস ---
class Premiam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_premium", description="Choose a plan and buy premium")
    async def buy_premium(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💎 Premium Access",
            description="1. Pay the amount via bKash/Nagad.\n2. Click the button below to submit TxnID.",
            color=0xFFD700
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1465990068224393343/1471035901735076007/GooglePay_QR.png?ex=698d7871&is=698c26f1&hm=bd1bda69ad37ab50e39f8ed7e33c151bdeeb35e50c305218b25a64d3c182dc0f&")
        await interaction.response.send_message(embed=embed, view=PremiumBuyView())

async def setup(bot):
    await bot.add_cog(Premiam(bot))
    
