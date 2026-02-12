import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import asyncio
import random
import datetime
from utils import load_config, save_config, get_theme_color

# --- হেল্পার: সার্ভার প্রিমিয়াম কিনা চেক ---
def is_server_premium(interaction: discord.Interaction):
    color = get_theme_color(interaction.guild.id)
    return color == discord.Color.gold()

# --- ১. ড্যাশবোর্ড মডাল ---
class GiveawayDashboardModal(Modal, title="💎 Premium Giveaway Settings"):
    def __init__(self):
        super().__init__()
        config = load_config()
        # সার্ভার স্পেসিফিক সেটিংস লোড করা উচিত, কিন্তু সিম্পল রাখতে গ্লোবাল সেটিংস রাখা হলো
        gw_data = config.get("giveaway_settings", {})

        self.title_in = TextInput(label="Giveaway Title", default=gw_data.get("title", "🎉 SPECIAL GIVEAWAY 🎉"), required=True)
        self.emoji_in = TextInput(label="Emoji", default=gw_data.get("emoji", "🎁"), required=True)
        self.gif_in = TextInput(label="Banner URL (Optional)", default=gw_data.get("gif_url", ""), required=False)
        
        self.add_item(self.title_in)
        self.add_item(self.emoji_in)
        self.add_item(self.gif_in)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        config["giveaway_settings"] = {
            "title": self.title_in.value,
            "emoji": self.emoji_in.value,
            "gif_url": self.gif_in.value
        }
        save_config(config)
        await interaction.response.send_message("✅ Settings Updated!", ephemeral=True)

# --- ২. গিভঅ্যাওয়ে সিস্টেম ---
class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway_dashboard", description="💎 [PREMIUM] Customize Giveaway")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_dashboard(self, interaction: discord.Interaction):
        if not is_server_premium(interaction):
            return await interaction.response.send_message("💎 **Premium Required!**\nThis server needs Premium to customize giveaways.", ephemeral=True)
        
        await interaction.response.send_modal(GiveawayDashboardModal())

    @app_commands.command(name="giveaway", description="🎉 Start a giveaway")
    @app_commands.describe(duration="Time (10m, 1h)", winners="Winners", prize="Prize")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        
        is_prem = is_server_premium(interaction)
        color = discord.Color.gold() if is_prem else discord.Color.blue()
        
        # ডিফল্ট সেটিংস
        gw_settings = {"title": "🎉 GIVEAWAY 🎉", "emoji": "🎁", "gif_url": None}

        # প্রিমিয়াম হলে কাস্টম সেটিংস
        if is_prem:
            config = load_config()
            if config.get("giveaway_settings"):
                gw_settings.update(config["giveaway_settings"])

        # সময় লজিক
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
        except:
            return await interaction.response.send_message("❌ Invalid Time! Use `10m`, `1h`.", ephemeral=True)

        end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        
        embed = discord.Embed(
            title=gw_settings["title"],
            description=f"React with {gw_settings['emoji']} to join!\n\n🎁 **Prize:** {prize}\n🏆 **Winners:** {winners}\n⏳ **Ends:** <t:{int(end_time.timestamp())}:R>",
            color=color
        )
        if is_prem and gw_settings["gif_url"]:
            embed.set_image(url=gw_settings["gif_url"])

        await interaction.response.send_message(f"✅ Giveaway Started!", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        try: await msg.add_reaction(gw_settings["emoji"])
        except: pass

        await asyncio.sleep(seconds)
        
        # উইনার লজিক
        try: msg = await interaction.channel.fetch_message(msg.id)
        except: return

        users = [u async for u in msg.reactions[0].users() if not u.bot]
        if len(users) < winners:
            await msg.edit(embed=discord.Embed(title="🚫 Cancelled (Not enough users)", color=discord.Color.red()))
            return

        winners_list = random.sample(users, winners)
        mentions = ", ".join([w.mention for w in winners_list])
        
        win_embed = discord.Embed(
            title="🎊 GIVEAWAY ENDED",
            description=f"🎁 **Prize:** {prize}\n👑 **Winners:** {mentions}",
            color=color
        )
        if is_prem and gw_settings["gif_url"]: win_embed.set_image(url=gw_settings["gif_url"])
        
        await msg.edit(embed=win_embed)
        await interaction.channel.send(f"Congratulations {mentions}! You won **{prize}**!")

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
        
