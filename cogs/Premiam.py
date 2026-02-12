import discord
from discord.ext import commands
from discord import app_commands
from utils import PremiumSelectionView, get_theme_color, load_config, PREMIUM_PRICE

class PremiumManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- বটের নাম পরিবর্তন (শুধুমাত্র প্রিমিয়াম সার্ভারে) ---
    async def update_bot_identity(self, interaction, is_premium):
        try:
            me = interaction.guild.me
            if me.guild_permissions.change_nickname:
                if is_premium:
                    if me.nick != "✨ Wow Premium":
                        await me.edit(nick="✨ Wow Premium")
                else:
                    if me.nick is not None:
                        await me.edit(nick=None) # নাম রিসেট
        except:
            pass

    # --- ১. প্রিমিয়াম কেনা ---
    @app_commands.command(name="buy_premium", description="🛒 Unlock Gold Theme & Features for this Server")
    async def buy_premium(self, interaction: discord.Interaction):
        # কালার চেক (সার্ভার প্রিমিয়াম হলে গোল্ড)
        color = get_theme_color(interaction.guild.id)
        
        embed = discord.Embed(
            title="👑 Server Premium Store",
            description=(
                f"Upgrade **{interaction.guild.name}** to Premium!\n\n"
                f"💸 **Price:** {PREMIUM_PRICE}\n\n"
                "**💎 Premium Benefits:**\n"
                "• ✨ Bot Name changes to **'Wow Premium'**\n"
                "• 🎨 All Embeds become **GOLD** color\n"
                "• 🎁 Custom Giveaway Settings (Banner, Emoji)\n"
                "• 🚀 Priority Support"
            ),
            color=color
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        await interaction.response.send_message(embed=embed, view=PremiumSelectionView())

    # --- ২. স্ট্যাটাস চেক ---
    @app_commands.command(name="premium_status", description="📊 Check Server Subscription Status")
    async def premium_status(self, interaction: discord.Interaction):
        config = load_config()
        guild_id = str(interaction.guild.id)
        
        # কালার লজিক
        theme_color = get_theme_color(interaction.guild.id)
        is_premium = (theme_color == discord.Color.gold())
        
        # নাম আপডেট করা
        await self.update_bot_identity(interaction, is_premium)
        
        embed = discord.Embed(title="📊 Server Status", color=theme_color)
        
        if is_premium:
            expiry = config["premium_servers"][guild_id]["expiry"].split("T")[0]
            embed.add_field(name="🏰 Server Plan", value=f"✅ **PREMIUM ACTIVE**\n📅 Exp: {expiry}", inline=False)
            embed.set_footer(text="✨ Premium is Active! Gold Theme Enabled.")
        else:
            embed.add_field(name="🏰 Server Plan", value="🟦 **Free Version**", inline=False)
            embed.set_footer(text="Use /buy_premium to upgrade this server!")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumManagement(bot))
