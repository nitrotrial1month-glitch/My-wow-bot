import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import datetime

class GiveawaySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="Start a professional giveaway")
    @app_commands.describe(
        duration="Time for the giveaway (e.g., 10s, 5m, 1h, 1d)",
        winners="Number of winners",
        prize="What is the prize?"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        # Time conversion
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]
        except (KeyError, ValueError):
            return await interaction.response.send_message("❌ Invalid time format! Use `s`, `m`, `h`, or `d` (e.g., 10m).", ephemeral=True)

        end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
        
        embed = discord.Embed(
            title="🎉 NEW GIVEAWAY 🎉",
            description=f"React with 🎁 to enter!\n\n**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(end_time.timestamp())}:R>",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Giveaway ends at")
        embed.timestamp = end_time

        await interaction.response.send_message(f"✅ Giveaway started for **{prize}**!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🎁")

        await asyncio.sleep(seconds)

        # Re-fetch message to get reactions
        message = await interaction.channel.fetch_message(message.id)
        users = [user async for user in message.reactions[0].users() if not user.bot]

        if len(users) < winners:
            return await interaction.channel.send(f"⚠️ Not enough participants to choose {winners} winners for **{prize}**.")

        winner_list = random.sample(users, winners)
        winner_mentions = ", ".join([winner.mention for winner in winner_list])

        win_embed = discord.Embed(
            title="🎊 GIVEAWAY ENDED 🎊",
            description=f"**Prize:** {prize}\n**Winners:** {winner_mentions}\n\nCongratulations to the winners!",
            color=discord.Color.green()
        )
        await message.edit(embed=win_embed)
        await interaction.channel.send(f"Congratulations {winner_mentions}! You won the **{prize}**! 🥳")

async def setup(bot):
    await bot.add_cog(GiveawaySystem(bot))
  
