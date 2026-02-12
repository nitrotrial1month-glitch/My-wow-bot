import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import asyncio
import random
import datetime

# utils থেকে কনফিগ এবং কালার লজিক ইমপোর্ট
from utils import load_config, save_config, get_theme_color

# --- হেল্পার: প্রিমিয়াম চেক ---
def is_premium(interaction: discord.Interaction):
    """
    চেক করবে ইউজার বা সার্ভার প্রিমিয়াম কিনা।
    যদি গোল্ড কালার রিটার্ন আসে, তার মানে প্রিমিয়াম আছে।
    """
    color = get_theme_color(interaction.user.id, interaction.guild.id)
    return color == discord.Color.gold()

# --- ১. ড্যাশবোর্ড মডাল (শুধুমাত্র প্রিমিয়াম ইউজারদের জন্য) ---
class GiveawayDashboardModal(Modal, title="💎 Premium Giveaway Settings"):
    def __init__(self):
        super().__init__()
        config = load_config()
        # আগের সেভ করা ডাটা লোড করা
        gw_data = config.get("giveaway_settings", {
            "title": "🎉 SPECIAL GIVEAWAY 🎉",
            "emoji": "🎁",
            "gif_url": ""
        })

        self.title_in = TextInput(
            label="Giveaway Title", 
            default=gw_data.get("title", "🎉 SPECIAL GIVEAWAY 🎉"),
            required=True
        )
        self.emoji_in = TextInput(
            label="Reaction Emoji (ID or Symbol)", 
            placeholder="🎁 or <:nitro:12345>", 
            default=gw_data.get("emoji", "🎁"),
            required=True
        )
        self.gif_in = TextInput(
            label="Banner Image/GIF URL (Optional)", 
            placeholder="https://example.com/banner.gif", 
            default=gw_data.get("gif_url", ""),
            required=False
        )
        
        self.add_item(self.title_in)
        self.add_item(self.emoji_in)
        self.add_item(self.gif_in)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        
        # সেটিংস আপডেট
        config["giveaway_settings"] = {
            "title": self.title_in.value,
            "emoji": self.emoji_in.value,
            "gif_url": self.gif_in.value if self.gif_in.value else None
        }
        
        save_config(config)
        await interaction.response.send_message("✅ **Premium Settings Updated!**\nYour next giveaways will use this custom style.", ephemeral=True)

# --- ২. মেইন গিভঅ্যাওয়ে সিস্টেম ---
class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 💎 PREMIUM COMMAND: Dashboard
    @app_commands.command(name="giveaway_dashboard", description="💎 [PREMIUM] Customize giveaway look")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_dashboard(self, interaction: discord.Interaction):
        # ১. প্রিমিয়াম চেক
        if not is_premium(interaction):
            return await interaction.response.send_message(
                "💎 **Premium Feature!**\nOnly **Premium Users/Servers** can customize giveaways.\nUse `/buy_premium` to unlock Gold features.", 
                ephemeral=True
            )
        
        # ২. মডাল ওপেন
        await interaction.response.send_modal(GiveawayDashboardModal())

    # 🆓 FREE COMMAND: Start Giveaway
    @app_commands.command(name="giveaway", description="🎉 Start a giveaway instantly")
    @app_commands.describe(duration="Time (e.g. 10m, 1h)", winners="Winner count", prize="Prize name")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        
        # ১. কালার এবং সেটিংস লজিক
        theme_color = get_theme_color(interaction.user.id, interaction.guild.id)
        is_prem = (theme_color == discord.Color.gold())

        # ডিফল্ট সেটিংস (ফ্রি ইউজারদের জন্য)
        gw_settings = {
            "title": "🎉 GIVEAWAY 🎉",
            "emoji": "🎉",
            "gif_url": None
        }

        # যদি প্রিমিয়াম হয়, তবে কাস্টম সেটিংস লোড করবে
        if is_prem:
            config = load_config()
            saved_settings = config.get("giveaway_settings", {})
            # যদি সেভ করা সেটিংস থাকে, তা ব্যবহার করবে
            if saved_settings:
                gw_settings.update(saved_settings)

        # ২. সময় কনভার্ট করা
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
        except:
            return await interaction.response.send_message("❌ ভুল সময়! এভাবে লিখুন: `10m`, `1h`, `1d`.", ephemeral=True)

        end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        
        # ৩. এমবেড তৈরি
        embed = discord.Embed(
            title=gw_settings["title"],
            description=(
                f"React with {gw_settings['emoji']} to enter!\n\n"
                f"🎁 **Prize:** {prize}\n"
                f"🏆 **Winners:** {winners}\n"
                f"⏳ **Ends:** <t:{int(end_time.timestamp())}:R>\n\n"
                f"Hosted by: {interaction.user.mention}"
            ),
            color=theme_color # ব্লু (ফ্রি) অথবা গোল্ড (প্রিমিয়াম)
        )
        
        # প্রিমিয়াম হলে ইমেজ দেখাবে
        if is_prem and gw_settings["gif_url"]:
            embed.set_image(url=gw_settings["gif_url"])
            
        embed.timestamp = end_time

        await interaction.response.send_message(f"✅ Giveaway for **{prize}** started!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        
        # ৪. রিঅ্যাকশন দেওয়া
        try:
            await message.add_reaction(gw_settings["emoji"])
        except:
            await interaction.channel.send(f"⚠️ Error: ইমোজি '{gw_settings['emoji']}' ব্যবহার করা যাচ্ছে না। ডিফল্ট ইমোজি ব্যবহার করুন।", delete_after=10)

        # ৫. অপেক্ষা (Timer)
        await asyncio.sleep(seconds)

        # ৬. রেজাল্ট
        try:
            message = await interaction.channel.fetch_message(message.id)
        except:
            return # মেসেজ ডিলিট হলে বাতিল

        # বট বাদে বাকিদের লিস্ট
        users = [user async for user in message.reactions[0].users() if not user.bot]

        if len(users) < winners:
            fail_embed = discord.Embed(
                title="🚫 Giveaway Cancelled", 
                description="Not enough participants entered.", 
                color=discord.Color.red()
            )
            return await message.edit(embed=fail_embed)

        # উইনার সিলেক্ট
        winner_list = random.sample(users, winners)
        winner_mentions = ", ".join([w.mention for w in winner_list])

        win_embed = discord.Embed(
            title="🎊 GIVEAWAY ENDED 🎊",
            description=f"🎁 **Prize:** {prize}\n👑 **Winners:** {winner_mentions}",
            color=theme_color
        )
        
        if is_prem and gw_settings["gif_url"]:
            win_embed.set_image(url=gw_settings["gif_url"])

        await message.edit(embed=win_embed)
        await interaction.channel.send(f"Congratulations {winner_mentions}! You won **{prize}**! 🥳")

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
        
