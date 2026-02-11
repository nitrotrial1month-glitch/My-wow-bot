import discord
from discord.ext import commands
from discord import app_commands
import datetime
# আপনার utils.py থেকে ফাংশনগুলো ইম্পোর্ট করা হচ্ছে
from utils import load_config, save_config 

# আপনার ডিসকোর্ড ইউজার আইডি নিশ্চিত করুন
OWNER_ID = 1311355680640208926 

# --- ১. ওনার ভেরিফিকেশন ভিউ (Admin Side) ---
class AdminVerifyView(discord.ui.View):
    def __init__(self, user_id, days, tx_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.days = days
        self.tx_id = tx_id

    @discord.ui.button(label="Confirm Payment", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()
        if "premium" not in config:
            config["premium"] = {}
            
        expiry = datetime.datetime.now() + datetime.timedelta(days=self.days)
        config["premium"][str(self.user_id)] = expiry.isoformat()
        save_config(config)

        # ইউজারকে ডাইরেক্ট মেসেজ (DM) পাঠানো
        user = interaction.client.get_user(self.user_id)
        if user:
            try:
                embed = discord.Embed(
                    title="🌟 Premium Activated!", 
                    description=f"Plan: **{self.days} Days**\nExpires: `{expiry.strftime('%Y-%m-%d')}`", 
                    color=discord.Color.gold()
                )
                await user.send(embed=embed)
            except: pass

        await interaction.response.edit_message(content=f"✅ Approved! Premium added to <@{self.user_id}>", view=None)

    @discord.ui.button(label="Cancel / Fake", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"❌ Payment rejected for <@{self.user_id}>", view=None)

# --- ২. পেমেন্ট ফর্ম (Modal) - টাইটেল ছোট করা হয়েছে এরর এড়াতে ---
class PaymentModal(discord.ui.Modal):
    def __init__(self, days):
        # টাইটেল ৪৫ অক্ষরের নিচে রাখা হয়েছে
        super().__init__(title=f'Premium - {days} Days Plan')
        self.days = days
        self.tx_id = discord.ui.TextInput(
            label='Transaction ID', 
            placeholder='Enter TxnID (e.g. BKT12345)', 
            required=True,
            min_length=5,
            max_length=50
        )

    async def on_submit(self, interaction: discord.Interaction):
        owner = interaction.client.get_user(OWNER_ID)
        if not owner:
            return await interaction.response.send_message("Owner unreachable!", ephemeral=True)

        embed = discord.Embed(title="💰 New Premium Request", color=discord.Color.blue())
        embed.add_field(name="User", value=f"{interaction.user.mention} (`{interaction.user.id}`)")
        embed.add_field(name="Plan", value=f"**{self.days} Days**")
        embed.add_field(name="Txn ID", value=f"`{self.tx_id.value}`")
        
        # ওনারের কাছে রিকোয়েস্ট পাঠানো
        await owner.send(embed=embed, view=AdminVerifyView(interaction.user.id, self.days, self.tx_id.value))
        await interaction.response.send_message("✅ Request sent! Please wait for owner verification.", ephemeral=True)

# --- ৩. সাবমিট বাটন ভিউ ---
class SubmitTxIDView(discord.ui.View):
    def __init__(self, days):
        super().__init__(timeout=None)
        self.days = days

    @discord.ui.button(label="Submit TxnID", style=discord.ButtonStyle.primary, emoji="📝")
    async def submit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Modal ওপেন করা হচ্ছে
        await interaction.response.send_modal(PaymentModal(self.days))

# --- ৪. প্ল্যান সিলেক্ট করার মেনু (Dropdown) ---
class PlanSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="Choose a Plan...",
        options=[
            discord.SelectOption(label="Basic (30 Days)", value="30", description="49 BDT", emoji="⭐"),
            discord.SelectOption(label="Standard (90 Days)", value="90", description="129 BDT", emoji="🌟"),
            discord.SelectOption(label="Legend (365 Days)", value="365", description="399 BDT", emoji="👑"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        days = int(select.values[0])
        
        embed = discord.Embed(
            title="💳 Complete Your Payment", 
            description=f"Plan: **{days} Days**\n\n**Instructions:**\n1. Send money via bKash/Nagad.\n2. Note down the TxnID.\n3. Click the button below to submit.",
            color=discord.Color.green()
        )
        # আপনার কিউআর কোড ইমেজ
        embed.set_image(url="https://cdn.discordapp.com/attachments/1465990068224393343/1471035901735076007/GooglePay_QR.png?ex=698d7871&is=698c26f1&hm=bd1bda69ad37ab50e39f8ed7e33c151bdeeb35e50c305218b25a64d3c182dc0f&")

        await interaction.response.edit_message(embed=embed, view=SubmitTxIDView(days))

# --- ৫. মেইন কগ ক্লাস ---
class PremiumManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_premium", description="Upgrade to premium access")
    async def buy_premium(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💎 Premium Membership",
            description="Select a plan from the dropdown to see payment methods.",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, view=PlanSelectView())

    @commands.hybrid_command(name="premium_status", description="Check your premium validity")
    async def premium_status(self, ctx):
        config = load_config()
        premium_data = config.get("premium", {})
        user_id = str(ctx.author.id)
        
        if user_id in premium_data:
            expiry = datetime.datetime.fromisoformat(premium_data[user_id])
            if datetime.datetime.now() < expiry:
                await ctx.send(f"🌟 Premium Status: **Active**\nExpires on: `{expiry.strftime('%Y-%m-%d')}`")
                return
        
        await ctx.send("❌ You don't have an active premium.")

async def setup(bot):
    await bot.add_cog(PremiumManager(bot))
