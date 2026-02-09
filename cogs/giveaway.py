import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View
import asyncio
import random
import datetime

# --- Giveaway Configuration ---
gw_config = {
    "title": "🎉 NEW GIVEAWAY 🎉",
    "color": discord.Color.gold(),
    "gif_url": None,
    "emoji": "🎁"
}

class GiveawayDashboardModal(Modal, title="Giveaway System Dashboard"):
    title_in = TextInput(label="Giveaway Title", default=gw_config["title"])
    emoji_in = TextInput(label="Reaction Emoji (Animated/Normal)", placeholder="e.g. <:nitro:123456789> or 🎁", default=gw_config["emoji"])
    gif_in = TextInput(label="GIF/Image URL", placeholder="https://example.com/image.gif", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        gw_config["title"] = self.title_in.value
        gw_config["emoji"] = self.emoji_in.value
        gw_config["gif_url"] = self.gif_in.value if self.gif_in.value else None
        await interaction.response.send_message("✅ Giveaway Dashboard Updated!", ephemeral=True)

class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway_dashboard", description="Customize giveaway title, emoji, and GIF")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GiveawayDashboardModal())

    @app_commands.command(name="giveaway", description="Start a customized giveaway")
    @app_commands.describe(duration="e.g. 10m, 1h, 1d", winners="Number of winners", prize="What is the prize?")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
        except:
            return await interaction.response.send_message("❌ Invalid format! Use `10m`, `1h` etc.", ephemeral=True)

        end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        
        embed = discord.Embed(
            title=gw_config["title"],
            description=f"React with {gw_config['emoji']} to enter!\n\n**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(end_time.timestamp())}:R>",
            color=gw_config["color"]
        )
        if gw_config["gif_url"]:
            embed.set_image(url=gw_config["gif_url"])
        embed.timestamp = end_time

        await interaction.response.send_message(f"✅ Giveaway for **{prize}** started!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        
        # Reaction handling (Normal or Animated Emoji)
        try:
            await message.add_reaction(gw_config["emoji"])
        except:
            await interaction.channel.send("⚠️ Error: Could not add reaction. Make sure the emoji ID is correct.")

        await asyncio.sleep(seconds)

        message = await interaction.channel.fetch_message(message.id)
        users = [user async for user in message.reactions[0].users() if not user.bot]

        if len(users) < winners:
            return await interaction.channel.send(f"⚠️ Not enough participants for **{prize}**.")

        winner_list = random.sample(users, winners)
        winner_mentions = ", ".join([w.mention for w in winner_list])

        win_embed = discord.Embed(
            title="🎊 GIVEAWAY ENDED 🎊",
            description=f"**Prize:** {prize}\n**Winners:** {winner_mentions}",
            color=discord.Color.green()
        )
        await message.edit(embed=win_embed)
        await interaction.channel.send(f"Congratulations {winner_mentions}! You won **{prize}**! 🥳")

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
    
