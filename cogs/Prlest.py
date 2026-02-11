import discord
from discord.ext import commands
from discord import app_commands

class PlanDetails(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.select(
        placeholder="Choose a Plan to see details...",
        options=[
            discord.SelectOption(label="Basic VIP", description="30 Days - 49 BDT", emoji="⭐"),
            discord.SelectOption(label="Standard Pro", description="90 Days - 129 BDT", emoji="🌟"),
            discord.SelectOption(label="Ultimate Legend", description="365 Days - 399 BDT", emoji="👑"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        plan = select.values[0]
        
        embed = discord.Embed(title=f"📋 Details for {plan}", color=discord.Color.gold())
        
        if plan == "Basic VIP":
            embed.description = (
                "**Duration:** 30 Days\n"
                "**Price:** 49 BDT\n\n"
                "**Features:**\n"
                "✅ Access to Custom Embeds\n"
                "✅ Advanced Slowmode Control\n"
                "✅ Bronze Badge on Profile"
            )
        elif plan == "Standard Pro":
            embed.description = (
                "**Duration:** 90 Days\n"
                "**Price:** 129 BDT\n\n"
                "**Features:**\n"
                "✅ All Basic Features\n"
                "✅ Anti-Link Bypass Settings\n"
                "✅ Pro Role in Support Server\n"
                "✅ Advanced Clear (Purge) Pro"
            )
        elif plan == "Ultimate Legend":
            embed.description = (
                "**Duration:** 365 Days (1 Year)\n"
                "**Price:** 399 BDT\n\n"
                "**Features:**\n"
                "✅ **Channel Nuke Access**\n"
                "✅ Everything in Pro & Basic\n"
                "✅ Early Access to New Features\n"
                "✅ Custom Bot Status (Optional)\n"
                "✅ Dedicated 24/7 Support"
            )
            
        await interaction.response.edit_message(embed=embed, view=self)

class PremiumList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="premium_list", description="View all Premium Plans and Facilities")
    async def premium_list(self, ctx):
        embed = discord.Embed(
            title="💎 Bot Premium Subscription Plans",
            description=(
                "Upgrade your server experience with our Premium features!\n\n"
                "**Available Plans:**\n"
                "⭐ **Basic VIP** - 49 BDT / Month\n"
                "🌟 **Standard Pro** - 129 BDT / 3 Months\n"
                "👑 **Ultimate Legend** - 399 BDT / Year\n\n"
                "**How to Buy?**\n"
                "Use `/buy_premium` to see the payment QR code and submit your TxnID."
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(text="Select a plan below for more details!")
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/625/625599.png") # VIP Icon

        view = PlanDetails()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(PremiumList(bot))
