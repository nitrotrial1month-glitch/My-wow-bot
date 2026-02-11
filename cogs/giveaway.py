import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import asyncio
import random
import datetime
# utils থেকে কনফিগ এবং প্রিমিয়াম চেকার ইমপোর্ট করা হলো
from utils import load_config, save_config, check_advanced_premium

# --- হেল্পার ফাংশন: প্রিমিয়াম চেক ---
def is_any_premium(interaction: discord.Interaction):
    """চেক করবে ইউজার অথবা সার্ভার - কারোর কি কোনো প্রিমিয়াম (Basic/Pro/Ultra) আছে?"""
    # ১. ইউজার চেক
    user_status = check_advanced_premium(interaction.user.id)
    if user_status["active"]: return True

    # ২. সার্ভার চেক
    server_status = check_advanced_premium(None, interaction.guild.id)
    if server_status["active"]: return True

    return False

# --- ১. ড্যাশবোর্ড মডাল (সেটিংস এডিট করার জন্য) ---
class GiveawayDashboardModal(Modal, title="💎 Premium Giveaway Dashboard"):
    def __init__(self):
        super().__init__()
        # বর্তমান কনফিগ লোড করে ডিফল্ট ভ্যালু হিসেবে দেখানো
        config = load_config()
        gw_data = config.get("giveaway_settings", {
            "title": "🎉 NEW GIVEAWAY 🎉",
            "emoji": "🎁",
            "gif_url": ""
        })

        self.title_in = TextInput(
            label="Giveaway Title", 
            default=gw_data.get("title", "🎉 NEW GIVEAWAY 🎉"),
            required=True
        )
        self.emoji_in = TextInput(
            label="Reaction Emoji", 
            placeholder="🎁 or <:nitro:12345>", 
            default=gw_data.get("emoji", "🎁"),
            required=True
        )
        self.gif_in = TextInput(
            label="Banner GIF/Image URL (Optional)", 
            placeholder="https://example.com/image.gif", 
            default=gw_data.get("gif_url", ""),
            required=False
        )
        
        # আইটেমগুলো মডালে যোগ করা
        self.add_item(self.title_in)
        self.add_item(self.emoji_in)
        self.add_item(self.gif_in)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        
        # নতুন সেটিংস সেভ করা
        config["giveaway_settings"] = {
            "title": self.title_in.value,
            "emoji": self.emoji_in.value,
            "gif_url": self.gif_in.value if self.gif_in.value else None
        }
        
        save_config(config)
        await interaction.response.send_message("✅ **Giveaway Settings Updated!**\nNow your giveaways will use this style.", ephemeral=True)

# --- ২. মেইন গিভঅ্যাওয়ে ক্লাস ---
class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 💎 PREMIUM COMMAND: Dashboard
    @app_commands.command(name="giveaway_dashboard", description="💎 [PREMIUM] Customize giveaway title, emoji & banner")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_dashboard(self, interaction: discord.Interaction):
        # প্রিমিয়াম চেক
        if not is_any_premium(interaction):
            return await interaction.response.send_message(
                "💎 **Premium Feature!**\nCustomizing the giveaway look is available for **Premium Members** only (Basic/Pro/Ultra).\nUse `/buy_premium` to unlock.", 
                ephemeral=True
            )
        
        await interaction.response.send_modal(GiveawayDashboardModal())

    # 🆓 FREE COMMAND: Start Giveaway (কিন্তু প্রিমিয়াম থাকলে কাস্টম ডিজাইন পাবে)
    @app_commands.command(name="giveaway", description="🎉 Start a giveaway")
    @app_commands.describe(duration="Duration (e.g. 10m, 1h, 1d)", winners="Number of winners", prize="Prize name")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        
        # কনফিগ লোড করা (যদি কাস্টম সেট করা থাকে)
        config = load_config()
        gw_settings = config.get("giveaway_settings", {
            "title": "🎉 NEW GIVEAWAY 🎉",
            "emoji": "🎁",
            "gif_url": None
        })

        # সময় গণনা (Time parsing)
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
        except:
            return await interaction.response.send_message("❌ Invalid time format! Use `10m`, `1h`, `1d`.", ephemeral=True)

        end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        
        # এমবেড তৈরি
        embed = discord.Embed(
            title=gw_settings["title"],
            description=(
                f"React with {gw_settings['emoji']} to enter!\n\n"
                f"🎁 **Prize:** {prize}\n"
                f"🏆 **Winners:** {winners}\n"
                f"⏳ **Ends:** <t:{int(end_time.timestamp())}:R>"
            ),
            color=discord.Color.gold()
        )
        
        if gw_settings["gif_url"]:
            embed.set_image(url=gw_settings["gif_url"])
            
        embed.timestamp = end_time

        await interaction.response.send_message(f"✅ Giveaway for **{prize}** started!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        
        # রিঅ্যাকশন যোগ করা
        try:
            await message.add_reaction(gw_settings["emoji"])
        except:
            await interaction.channel.send(f"⚠️ Error: I couldn't add the reaction '{gw_settings['emoji']}'. Please check the emoji ID in dashboard.")

        # টাইমার লুপ (অপেক্ষা)
        await asyncio.sleep(seconds)

        # রেজাল্ট বের করা
        try:
            message = await interaction.channel.fetch_message(message.id)
        except:
            return # মেসেজ ডিলিট হয়ে গেলে আর কিছু করার নেই

        users = [user async for user in message.reactions[0].users() if not user.bot]

        if len(users) < winners:
            fail_embed = discord.Embed(title="🚫 Giveaway Cancelled", description="Not enough participants entered.", color=discord.Color.red())
            return await message.edit(embed=fail_embed)

        winner_list = random.sample(users, winners)
        winner_mentions = ", ".join([w.mention for w in winner_list])

        win_embed = discord.Embed(
            title="🎊 GIVEAWAY ENDED 🎊",
            description=f"🎁 **Prize:** {prize}\n👑 **Winners:** {winner_mentions}",
            color=discord.Color.green()
        )
        if gw_settings["gif_url"]:
            win_embed.set_image(url=gw_settings["gif_url"])

        await message.edit(embed=win_embed)
        await interaction.channel.send(f"Congratulations {winner_mentions}! You won **{prize}**! 🥳")

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
