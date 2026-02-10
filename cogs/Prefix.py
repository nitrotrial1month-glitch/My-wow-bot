import discord
from discord.ext import commands
from discord import app_commands
import json

class PrefixSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_prefix", description="Change the bot's prefix for this server")
    @app_commands.describe(new_prefix="The new prefix (e.g. ?, ., $)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_prefix(self, interaction: discord.Interaction, new_prefix: str):
        if len(new_prefix) > 5:
            return await interaction.response.send_message("❌ Prefix is too long! Keep it under 5 characters.", ephemeral=True)

        # JSON ফাইলে প্রিফিক্স সেভ করা
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)

        prefixes[str(interaction.guild.id)] = new_prefix

        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

        await interaction.response.send_message(f"✅ Prefix has been changed to: `{new_prefix}`")

async def setup(bot):
    await bot.add_cog(PrefixSystem(bot))
  
