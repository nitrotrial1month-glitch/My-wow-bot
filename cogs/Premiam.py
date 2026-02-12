import discord
from discord.ext import commands
from discord import app_commands
from utils import PremiumSelectionView, get_theme_color, load_config

# আপনার পেমেন্ট QR কোড
QR_CODE_URL = "https://cdn.discordapp.com/attachments/1465990068224393343/1471035901735076007/GooglePay_QR.png?ex=698ec9f1&is=698d7871&hm=9c367f3889c5ccb9946a1b2c42a792ac291d415518ec7dd2a08ce93f9be4e6c7&"

class PremiumManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. বটের নাম ও পারমিশন চেক ফাংশন ---
    async def update_bot_identity(self, interaction, is_premium):
        """
        রিটার্ন করবে: True (যদি পারমিশন থাকে), False (যদি পারমিশন না থাকে)
        """
        try:
            me = interaction.guild.me
            
            # পারমিশন চেক: বটের কি নাম পাল্টানোর অনুমতি আছে?
            if not me.guild_permissions.change_nickname:
                return False # ❌ পারমিশন নেই

            # নাম পরিবর্তন লজিক
            if is_premium:
                if me.nick != "✨ Wow Premium":
                    await me.edit(nick="✨ Wow Premium")
            else:
                if me.nick is not None:
                    await me.edit(nick=None)
            
            return True # ✅ সব ঠিক আছে

        except Exception as e:
            print(f"Name Change Error: {e}")
            return False

    # ====================================================
    # 2. প্রিমিয়াম কেনার কমান্ড (QR Code সহ)
    # ====================================================
    @app_commands.command(name="buy_premium", description="🛒 Upgrade Server to Premium (QR Code Inside)")
    async def buy_premium(self, interaction: discord.Interaction):
        color = get_theme_color(interaction.guild.id)
        
        embed = discord.Embed(
            title="👑 Server Premium Store",
            description=(
                f"Upgrade **{interaction.guild.name}** to Premium!\n\n"
                "**💸 Price:** 100 Taka/Month\n"
                "**📱 Payment:** Scan the QR Code below 👇\n\n"
                "**💎 Premium Benefits:**\n"
                "• ✨ Bot Name changes to **'Wow Premium'**\n"
                "• 🎨 All Embeds become **GOLD** color\n"
                "• 🎁 Custom Giveaway Settings\n"
                "• 🚀 Priority Support"
            ),
            color=color
        )
        
        # QR Code ইমেজ সেট করা
        embed.set_image(url=QR_CODE_URL)
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            
        embed.set_footer(text="After payment, click the button below.")
        
        await interaction.response.send_message(embed=embed, view=PremiumSelectionView())

    # ====================================================
    # 3. স্ট্যাটাস চেক কমান্ড (পারমিশন ওয়ার্নিং সহ)
    # ====================================================
    @app_commands.command(name="premium_status", description="📊 Check Server Subscription Status")
    async def premium_status(self, interaction: discord.Interaction):
        config = load_config()
        guild_id = str(interaction.guild.id)
        
        # ১. কালার এবং স্ট্যাটাস চেক
        theme_color = get_theme_color(interaction.guild.id)
        is_premium = (theme_color == discord.Color.gold())
        
        # ২. নাম আপডেট এবং পারমিশন চেক
        has_permission = await self.update_bot_identity(interaction, is_premium)
        
        # ৩. এমবেড তৈরি
        embed = discord.Embed(title="📊 Server Status", color=theme_color)
        
        if is_premium:
            try:
                expiry = config["premium_servers"][guild_id]["expiry"].split("T")[0]
            except:
                expiry = "Active"
                
            embed.add_field(name="🏰 Server Plan", value=f"✅ **PREMIUM ACTIVE**\n📅 Exp: {expiry}", inline=False)
            
            # যদি পারমিশন থাকে
            if has_permission:
                embed.add_field(name="✨ Bot Name", value="Changed to **'Wow Premium'**", inline=False)
            else:
                # ⚠️ যদি পারমিশন না থাকে (লাল ওয়ার্নিং)
                embed.add_field(
                    name="⚠️ Permission Missing", 
                    value="❌ I cannot change my nickname!\nPlease enable **'Change Nickname'** permission for my role.", 
                    inline=False
                )
            
            embed.set_footer(text="✨ Premium is Active! Gold Theme Enabled.")
        else:
            embed.add_field(name="🏰 Server Plan", value="🟦 **Free Version**", inline=False)
            embed.set_footer(text="Use /buy_premium to upgrade this server!")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumManagement(bot))
    
