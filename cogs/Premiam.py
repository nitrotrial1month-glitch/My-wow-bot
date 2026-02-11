import discord
from discord.ext import commands
from discord import app_commands
import datetime
from utils import load_config, save_config 

OWNER_ID = 1311355680640208926 

# --- ১. ওনার সাইড (Admin) ---
class AdminVerifyView(discord.ui.View):
    def __init__(self, user_id, days):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.days = days

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="app_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()
        if "premium" not in config: config["premium"] = {}
        expiry = datetime.datetime.now() + datetime.timedelta(days=self.days)
        config["premium"][str(self.user_id)] = expiry.isoformat()
        save_config(config)
        await interaction.response.edit_message(content=f"✅ Done for <@{self.user_id}>", view=None)

# --- ২. পেমেন্ট ফর্ম (Modal) - এখানে আইডি ছোট রাখা হয়েছে ---
class PaymentModal(discord.ui.Modal):
    def __init__(self, days):
        # টাইটেল একদম ছোট রাখা হলো এরর এড়াতে
        super().__init__(title="Payment Info", custom_id="pay_modal") 
        self.days = days
        self.tx_id = discord.ui.TextInput(
            label='Transaction ID',
            placeholder='Enter TxnID here',
            min_length=5,
            max_length=30,
            custom_id="tx_input"
        )

    async def on_submit(self, interaction: discord.Interaction):
        owner = interaction.client.get_user(OWNER_ID)
        if not owner:
            return await interaction.response.send_message("Owner Offline", ephemeral=True)
            
        embed = discord.Embed(title="Premium Request", color=discord.Color.blue())
        embed.add_field(name="User", value=interaction.user.mention)
        embed.add_field(name="Plan", value=f"{self.days} Days")
        embed.add_field(name="TxnID", value=self.tx_id.value)
        
        await owner.send(embed=embed, view=AdminVerifyView(interaction.user.id, self.days))
        await interaction.response.send_message("✅ Sent!", ephemeral=True)

# --- ৩. মেইন বাই ভিউ ---
class PremiumBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="30 Days", style=discord.ButtonStyle.primary, custom_id="btn_30")
    async def btn_30(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(30))

    @discord.ui.button(label="90 Days", style=discord.ButtonStyle.primary, custom_id="btn_90")
    async def btn_90(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(90))

    @discord.ui.button(label="365 Days", style=discord.ButtonStyle.primary, custom_id="btn_365")
    async def btn_365(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(365))

class Premiam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_premium", description="Upgrade plan")
    async def buy_premium(self, interaction: discord.Interaction):
        embed = discord.Embed(title="💎 Premium", description="Click a button to pay", color=0xFFD700)
        await interaction.response.send_message(embed=embed, view=PremiumBuyView())

async def setup(bot):
    await bot.add_cog(Premiam(bot))
    
