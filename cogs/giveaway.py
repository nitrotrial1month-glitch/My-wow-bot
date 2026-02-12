import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import asyncio
import random
import datetime
from utils import load_config, save_config, get_theme_color

# --- হেল্পার ফাংশন ---
def is_server_premium(interaction: discord.Interaction):
    if not interaction.guild: return False
    # utils.py থেকে কালার চেক করে বুঝবো প্রিমিয়াম কিনা
    color = get_theme_color(interaction.guild.id)
    return color == discord.Color.gold()

# --- ড্যাশবোর্ড মডাল (শুধুমাত্র প্রিমিয়ামদের জন্য) ---
class GiveawayDashboardModal(Modal, title="💎 Premium Giveaway Settings"):
    def __init__(self):
        super().__init__()
        config = load_config()
        gw_data = config.get("giveaway_settings", {})

        self.emoji_in = TextInput(label="Emoji", default=gw_data.get("emoji", "🎁"), required=True)
        self.gif_in = TextInput(label="Banner URL (Optional)", default=gw_data.get("gif_url", ""), required=False)
        
        self.add_item(self.emoji_in)
        self.add_item(self.gif_in)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        current = config.get("giveaway_settings", {})
        config["giveaway_settings"] = {
            "emoji": self.emoji_in.value,
            "gif_url": self.gif_in.value,
            "title": current.get("title", "Giveaway")
        }
        save_config(config)
        await interaction.response.send_message("✅ **Premium Settings Updated!**", ephemeral=True)

# --- মেইন সিস্টেম ---
class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ১. ড্যাশবোর্ড কমান্ড
    @app_commands.command(name="giveaway_dashboard", description="💎 [PREMIUM] Setup Custom Banner & Emoji")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_dashboard(self, interaction: discord.Interaction):
        if not is_server_premium(interaction):
            return await interaction.response.send_message("💎 **Premium Required!**\nUnlock Custom Banner with `/buy_premium`.", ephemeral=True)
        
        await interaction.response.send_modal(GiveawayDashboardModal())

    # ২. গিভঅ্যাওয়ে কমান্ড
    @app_commands.command(name="giveaway", description="🎉 Start a Giveaway")
    @app_commands.describe(duration="Time (e.g. 10m, 1h)", winners="Winners", prize="Prize")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        
        # --- প্রিমিয়াম চেক ---
        is_prem = is_server_premium(interaction)
        
        # কালার লজিক (Premium = Gold, Free = Blue)
        color = discord.Color.gold() if is_prem else discord.Color.blue()
        
        # সেটিংস লোড
        gw_settings = {"emoji": "🎁", "gif_url": None}
        if is_prem:
            config = load_config()
            if config.get("giveaway_settings"):
                gw_settings.update(config["giveaway_settings"])

        # সময় ঠিক করা
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
        except:
            return await interaction.response.send_message("❌ Time Error! Use: `10m`, `1h`.", ephemeral=True)

        end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        end_timestamp = int(end_time.timestamp())

        # --- এমবেড ডিজাইন (সুন্দর এবং ক্লিন) ---
        description = (
            f"### {gw_settings['emoji']} **{prize}** {gw_settings['emoji']}\n\n"
            f"• **Winners:** {winners}\n"
            f"• **Ends:** <t:{end_timestamp}:R>\n"
            f"• **Hosted by:** {interaction.user.mention}\n\n"
            f"React with {gw_settings['emoji']} to join!"
        )

        embed = discord.Embed(description=description, color=color)
        embed.set_footer(text=f"Ends at | {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # প্রিমিয়াম হলে কাস্টম ব্যানার দেখাবে, না হলে দেখাবে না
        if is_prem and gw_settings["gif_url"]: 
            embed.set_image(url=gw_settings["gif_url"])

        # মেসেজ পাঠানো
        await interaction.response.send_message("✅ Giveaway Created!", ephemeral=True)
        msg = await interaction.channel.send(content="🎉 **GIVEAWAY** 🎉", embed=embed)
        
        try: await msg.add_reaction(gw_settings['emoji'])
        except: pass

        # টাইমার
        await asyncio.sleep(seconds)
        
        # রেজাল্ট
        try: msg = await interaction.channel.fetch_message(msg.id)
        except: return

        users = [u async for u in msg.reactions[0].users() if not u.bot]
        
        if len(users) < winners:
            fail_embed = discord.Embed(title="🚫 Cancelled", description="Not enough participants.", color=discord.Color.red())
            await msg.edit(embed=fail_embed)
            return

        winners_list = random.sample(users, winners)
        mentions = ", ".join([w.mention for w in winners_list])
        
        win_embed = discord.Embed(
            title="🎉 Giveaway Ended",
            description=f"🎁 **Prize:** {prize}\n👑 **Winner(s):** {mentions}",
            color=color
        )
        if is_prem and gw_settings["gif_url"]: win_embed.set_image(url=gw_settings["gif_url"])
        
        await msg.edit(content="🎊 **CONGRATULATIONS!** 🎊", embed=win_embed)
        await interaction.channel.send(f"Congratulations {mentions}! You won **{prize}**!")

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
            
