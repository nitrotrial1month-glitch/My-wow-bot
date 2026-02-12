import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import asyncio
import random
import datetime
from utils import load_config, save_config, get_theme_color

# --- হেল্পার ---
def is_server_premium(interaction: discord.Interaction):
    if not interaction.guild: return False
    color = get_theme_color(interaction.guild.id)
    return color == discord.Color.gold()

# --- ড্যাশবোর্ড মডাল ---
class GiveawayDashboardModal(Modal, title="💎 Premium Giveaway Settings"):
    def __init__(self):
        super().__init__()
        config = load_config()
        gw_data = config.get("giveaway_settings", {})

        self.title_in = TextInput(label="Custom Title", default=gw_data.get("title", "🎉 SPECIAL GIVEAWAY 🎉"), required=True)
        self.emoji_in = TextInput(label="Custom Emoji", default=gw_data.get("emoji", "🎁"), required=True)
        self.gif_in = TextInput(label="Banner Image URL (Big Image)", default=gw_data.get("gif_url", ""), required=False)
        
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
        await interaction.response.send_message("✅ **Premium Settings Updated!**", ephemeral=True)

# --- মেইন সিস্টেম ---
class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway_dashboard", description="💎 [PREMIUM] Customize Giveaway Look")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_dashboard(self, interaction: discord.Interaction):
        if not is_server_premium(interaction):
            return await interaction.response.send_message("💎 **Premium Feature!**\nUse `/buy_premium` to unlock Custom Title & Banners.", ephemeral=True)
        
        await interaction.response.send_modal(GiveawayDashboardModal())

    @app_commands.command(name="giveaway", description="🎉 Start a stylish giveaway")
    @app_commands.describe(duration="Time (10m, 1h)", winners="Winners", prize="Prize")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        
        # ১. প্রিমিয়াম চেক
        is_prem = is_server_premium(interaction)
        color = discord.Color.gold() if is_prem else discord.Color.from_rgb(0, 153, 255) # সুন্দর স্কাই ব্লু (ফ্রি)
        
        # ২. ডিফল্ট সেটিংস (ফ্রি এবং সবার জন্য)
        gw_settings = {
            "title": "🎉 **COMMUNITY GIVEAWAY** 🎉", # ডিফল্ট সুন্দর টাইটেল
            "emoji": "🎁",
            "gif_url": None,
            "thumbnail": "https://cdn-icons-png.flaticon.com/512/4213/4213958.png" # একটি সুন্দর গিফট আইকন (সবার জন্য)
        }

        # ৩. প্রিমিয়াম হলে কাস্টম সেটিংস লোড হবে
        if is_prem:
            config = load_config()
            if config.get("giveaway_settings"):
                saved = config["giveaway_settings"]
                gw_settings["title"] = saved.get("title", gw_settings["title"])
                gw_settings["emoji"] = saved.get("emoji", gw_settings["emoji"])
                gw_settings["gif_url"] = saved.get("gif_url") # বড় ব্যানার শুধু প্রিমিয়ামে

        # ৪. সময় ক্যালকুলেশন
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
        except:
            return await interaction.response.send_message("❌ Time format error! Use: `10m`, `1h`, `1d`.", ephemeral=True)

        end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        
        # ৫. এমবেড ডিজাইন (স্টাইলিশ)
        embed = discord.Embed(
            title=gw_settings["title"],
            description=f"React with {gw_settings['emoji']} to enter!\n─────────────────────",
            color=color
        )

        # সুন্দর ফিল্ড ডিজাইন
        embed.add_field(name="🎁 Prize", value=f"**{prize}**", inline=False)
        embed.add_field(name="🏆 Winners", value=f"`{winners}` Person(s)", inline=True)
        embed.add_field(name="⏳ Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        
        # থাম্বনেইল (ছোট ছবি) - এটি এখন ফ্রি ইউজাররাও পাবে!
        embed.set_thumbnail(url=gw_settings["thumbnail"])
        
        # ফুটার
        embed.set_footer(text=f"Hosted by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.timestamp = end_time

        # বড় ব্যানার (শুধুমাত্র প্রিমিয়াম)
        if is_prem and gw_settings["gif_url"]: 
            embed.set_image(url=gw_settings["gif_url"])

        # মেসেজ পাঠানো
        await interaction.response.send_message(f"✅ Giveaway Created!", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        
        try: await msg.add_reaction(gw_settings["emoji"])
        except: pass

        # টাইমার
        await asyncio.sleep(seconds)
        
        # রেজাল্ট প্রসেসিং
        try: msg = await interaction.channel.fetch_message(msg.id)
        except: return

        users = [u async for u in msg.reactions[0].users() if not u.bot]
        
        if len(users) < winners:
            fail_embed = discord.Embed(
                title="🚫 Giveaway Cancelled", 
                description="Not enough participants entered.", 
                color=discord.Color.red()
            )
            await msg.edit(embed=fail_embed)
            return

        winners_list = random.sample(users, winners)
        mentions = ", ".join([w.mention for w in winners_list])
        
        # উইনার এমবেড
        win_embed = discord.Embed(
            title="🎊 **GIVEAWAY ENDED** 🎊",
            description=f"🎁 **Prize:** {prize}\n👑 **Winners:** {mentions}",
            color=discord.Color.green()
        )
        # জেতার পরেও থাম্বনেইল থাকবে
        win_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/744/744922.png") 
        
        await msg.edit(embed=win_embed)
        await interaction.channel.send(f"Congratulations {mentions}! You won **{prize}**! 🥳")

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
        
