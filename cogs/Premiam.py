import discord
from discord.ext import commands
from discord import app_commands
import datetime
from utils import load_config, save_config 

OWNER_ID = 1311355680640208926 

# --- ১. ওনার ভেরিফিকেশন ভিউ (অ্যাডমিন কনফার্মেশন) ---
class AdminVerifyView(discord.ui.View):
    def __init__(self, user_id, days, tx_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.days = days
        self.tx_id = tx_id

    @discord.ui.button(label="Confirm Payment", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = load_config()
        if "premium" not in config: config["premium"] = {}
            
        expiry = datetime.datetime.now() + datetime.timedelta(days=self.days)
        config["premium"][str(self.user_id)] = expiry.isoformat()
        save_config(config)

        user = interaction.client.get_user(self.user_id)
        if user:
            try:
                embed = discord.Embed(title="🌟 Premium Activated!", 
                                    description=f"Plan: **{self.days} Days**\nExpires on: `{expiry.strftime('%Y-%m-%d')}`", 
                                    color=discord.Color.gold())
                await user.send(embed=embed)
            except: pass

        await interaction.response.edit_message(content=f"✅ Approved! Premium added to <@{self.user_id}>", view=None)

    @discord.ui.button(label="Cancel / Fake", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"❌ Payment rejected for <@{self.user_id}>", view=None)

# --- ২. পেমেন্ট ফর্ম (Transaction ID সাবমিট) ---
class PaymentModal(discord.ui.Modal):
    def __init__(self, days):
        super().__init__(title=f'Submit Payment - {days} Days Plan')
        self.days = days
        self.tx_id = discord.ui.TextInput(label='Transaction ID', placeholder='Enter TxnID (e.g. BKT12345)', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner = interaction.client.get_user(OWNER_ID)
        if not owner: return await interaction.response.send_message("Owner unreachable!", ephemeral=True)

        embed = discord.Embed(title="💰 New Premium Request", color=discord.Color.blue())
        embed.add_field(name="User", value=f"{interaction.user.mention}")
        embed.add_field(name="Plan Chosen", value=f"**{self.days} Days**")
        embed.add_field(name="Txn ID", value=f"`{self.tx_id.value}`")
        
        await owner.send(embed=embed, view=AdminVerifyView(interaction.user.id, self.days, self.tx_id.value))
        await interaction.response.send_message("✅ Your request has been sent! Please wait for owner verification.", ephemeral=True)

# --- ৩. প্ল্যান সিলেক্ট করার মেনু (Dropdown) ---
class PlanSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="Select a Premium Plan...",
        options=[
            discord.SelectOption(label="Basic (1 Month)", value="30", description="49 BDT - 30 Days Access", emoji="⭐"),
            discord.SelectOption(label="Standard (3 Months)", value="90", description="129 BDT - 90 Days Access", emoji="🌟"),
            discord.SelectOption(label="Legend (1 Year)", value="365", description="399 BDT - 365 Days Access", emoji="👑"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        days = int(select.values[0])
        
        embed = discord.Embed(title="💳 Payment Details", 
                            description=f"You have selected the **{days} Days Plan**.\n\n"
                                        "**Please Pay:**\n"
                                        f"- Amount: `{select.options[0].description.split(' - ')[0]}`\n"
                                        "- Method: bKash / Nagad (Personal)\n\n"
                                        "Scan the QR code below and then click 'Submit TxnID'.",
                            color=discord.Color.green())
        
        # QR Code Link
        embed.set_image(url="https://cdn.discordapp.com/attachments/1465990068224393343/1471035901735076007/GooglePay_QR.png?ex=698d7871&is=698c26f1&hm=bd1bda69ad37ab50e39f8ed7e33c151bdeeb35e50c305218b25a64d3c182dc0f&")

        view = discord.ui.View()
        btn = discord.ui.Button(label="Submit TxnID", style=discord.ButtonStyle.primary, emoji="📝")
        
        async def btn_callback(inter):
            await inter.response.send_modal(PaymentModal(days))
        
        btn.callback = btn_callback
        view.add_item(btn)
        
        await interaction.response.edit_message(embed=embed, view=view)

# --- ৪. মেইন কগ ক্লাস ---
class PremiumManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy_premium", description="Select a plan and upgrade to premium")
    async def buy_premium(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💎 Upgrade to Premium",
            description="Choose your desired plan from the dropdown menu below to see payment details.",
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
                await ctx.send(f"🌟 Your premium is **Active** until: `{expiry.strftime('%Y-%m-%d')}`")
                return
        
        await ctx.send("❌ You don't have an active premium. Use `/buy_premium` to upgrade!")

async def setup(bot):
    await bot.add_cog(PremiumManager(bot))
        
