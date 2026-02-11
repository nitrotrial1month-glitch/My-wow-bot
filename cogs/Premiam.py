import discord
from discord.ext import commands
from discord import app_commands
import datetime
# utils থেকে প্রয়োজনীয় ফাংশনগুলো ইম্পোর্ট করা হলো
from utils import load_config, save_config 

OWNER_ID = 1311355680640208926 

# --- ওনার ভেরিফিকেশন ভিউ ---
class AdminVerifyView(discord.ui.View):
    def __init__(self, user_id, days, tx_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.days = days
        self.tx_id = tx_id

    @discord.ui.button(label="Confirm Payment", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # config.json লোড করা হচ্ছে
        config = load_config()
        
        # প্রিমিয়াম সেকশন না থাকলে তৈরি করা
        if "premium" not in config:
            config["premium"] = {}
            
        expiry = datetime.datetime.now() + datetime.timedelta(days=self.days)
        # ডাটা config.json এ সেভ হচ্ছে
        config["premium"][str(self.user_id)] = expiry.isoformat()
        save_config(config)

        # ইউজারকে জানানো
        user = interaction.client.get_user(self.user_id)
        if user:
            try:
                embed = discord.Embed(title="🌟 Premium Activated!", 
                                    description=f"Your premium has been activated for {self.days} days.\nExpires on: {expiry.strftime('%Y-%m-%d')}", 
                                    color=discord.Color.gold())
                await user.send(embed=embed)
            except: pass

        await interaction.response.edit_message(content=f"✅ Verified! Premium added to <@{self.user_id}>", view=None)

    @discord.ui.button(label="Cancel / Fake", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"❌ Payment rejected for <@{self.user_id}>", view=None)

# --- ইউজার ট্রানজেকশন ফরম ---
class PaymentModal(discord.ui.Modal, title='Submit Payment Details'):
    tx_id = discord.ui.TextInput(label='Transaction ID', placeholder='Enter the TxnID', required=True)
    plan = discord.ui.TextInput(label='Plan (Days)', placeholder='30, 90, or 365', default='30', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner = interaction.client.get_user(OWNER_ID)
        if not owner:
            return await interaction.response.send_message("Owner not found!", ephemeral=True)

        embed = discord.Embed(title="💰 New Premium Request", color=discord.Color.blue())
        embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})")
        embed.add_field(name="Txn ID", value=self.tx_id.value)
        embed.add_field(name="Requested Plan", value=f"{self.plan.value} Days")
        
        await owner.send(embed=embed, view=AdminVerifyView(interaction.user.id, int(self.plan.value), self.tx_id.value))
        await interaction.response.send_message("✅ Your request sent! Wait for owner verification.", ephemeral=True)

class PremiumManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_premium", description="Buy bot premium and see QR code")
    async def buy_premium(self, interaction: discord.Interaction):
        embed = discord.Embed(title="💎 Get Premium Access", 
                            description="Scan the QR code below to pay. Then click the button to submit TxnID.",
                            color=discord.Color.purple())
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/1465990068224393343/1471035901735076007/GooglePay_QR.png?ex=698d7871&is=698c26f1&hm=bd1bda69ad37ab50e39f8ed7e33c151bdeeb35e50c305218b25a64d3c182dc0f&") 
        
        view = discord.ui.View()
        btn = discord.ui.Button(label="Submit Transaction ID", style=discord.ButtonStyle.primary, emoji="📝")
        
        async def btn_callback(inter):
            await inter.response.send_modal(PaymentModal())
        
        btn.callback = btn_callback
        view.add_item(btn)
        await interaction.response.send_message(embed=embed, view=view)

    @commands.hybrid_command(name="premium_status", description="Check your premium validity")
    async def premium_status(self, ctx):
        config = load_config()
        premium_data = config.get("premium", {})
        user_id = str(ctx.author.id)
        
        if user_id in premium_data:
            expiry = datetime.datetime.fromisoformat(premium_data[user_id])
            if datetime.datetime.now() < expiry:
                await ctx.send(f"🌟 Your premium is **Active** until: `{expiry.strftime('%Y-%m-%d')}`")
                return
        
        await ctx.send("❌ You don't have an active premium.")

async def setup(bot):
    await bot.add_cog(PremiumManager(bot))
        
