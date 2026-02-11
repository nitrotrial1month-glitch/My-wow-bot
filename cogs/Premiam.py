import discord
from discord.ext import commands
from discord import app_commands
import datetime
from utils import load_config, save_config 

OWNER_ID = 1311355680640208926 

# --- ১. ওনার ভেরিফিকেশন ভিউ ---
class AdminVerifyView(discord.ui.View):
    def __init__(self, user_id, days):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.days = days

    @discord.ui.button(label="Approve Payment", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()
        if "premium" not in config: config["premium"] = {}
        expiry = datetime.datetime.now() + datetime.timedelta(days=self.days)
        config["premium"][str(self.user_id)] = expiry.isoformat()
        save_config(config)
        await interaction.response.edit_message(content=f"✅ Approved for <@{self.user_id}>", view=None)

# --- ২. পেমেন্ট ফর্ম (Modal) ---
class PaymentModal(discord.ui.Modal):
    def __init__(self, days):
        super().__init__(title="Submit Transaction ID")
        self.days = days
        self.tx_id = discord.ui.TextInput(
            label='Transaction ID (TxnID)', 
            placeholder='e.g. BKX82910...',
            required=True
        )

    async def on_submit(self, interaction: discord.Interaction):
        owner = interaction.client.get_user(OWNER_ID)
        if not owner:
            return await interaction.response.send_message("Owner is offline!", ephemeral=True)
            
        embed = discord.Embed(title="💰 New Premium Request", color=discord.Color.blue())
        embed.add_field(name="User", value=interaction.user.mention)
        embed.add_field(name="Plan", value=f"{self.days} Days")
        embed.add_field(name="TxnID", value=self.tx_id.value)
        
        await owner.send(embed=embed, view=AdminVerifyView(interaction.user.id, self.days))
        await interaction.response.send_message("✅ Request sent to owner!", ephemeral=True)

# --- ৩. মেইন বাই ভিউ (৩টি আলাদা বাটন) ---
class PremiumBuyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="30 Days - 49 BDT", style=discord.ButtonStyle.primary, emoji="⭐")
    async def basic_plan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(30))

    @discord.ui.button(label="90 Days - 129 BDT", style=discord.ButtonStyle.primary, emoji="🌟")
    async def standard_plan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(90))

    @discord.ui.button(label="365 Days - 399 BDT", style=discord.ButtonStyle.primary, emoji="👑")
    async def legend_plan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PaymentModal(365))

# --- ৪. মেইন কগ ---
class PremiumManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_premium", description="Choose a plan and buy premium")
    async def buy_premium(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💎 Get Premium Access",
            description="1. Scan the QR code below.\n2. Pay the amount for your plan.\n3. Click the button below to submit TxnID.",
            color=discord.Color.gold()
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1465990068224393343/1471035901735076007/GooglePay_QR.png?ex=698d7871&is=698c26f1&hm=bd1bda69ad37ab50e39f8ed7e33c151bdeeb35e50c305218b25a64d3c182dc0f&")
        await interaction.response.send_message(embed=embed, view=PremiumBuyView())

async def setup(bot):
    await bot.add_cog(PremiumManager(bot))
