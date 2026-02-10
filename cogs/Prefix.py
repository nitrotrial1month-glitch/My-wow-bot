import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class PrefixSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_prefix", description="Set a custom prefix for this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_prefix(self, interaction: discord.Interaction, new_prefix: str):
        # ১. ফাইলটি আছে কি না চেক করা
        if not os.path.exists('prefixes.json'):
            with open('prefixes.json', 'w') as f:
                json.dump({}, f)

        # ২. বর্তমান ডাটা পড়া
        with open('prefixes.json', 'r') as f:
            try:
                prefixes = json.load(f)
            except json.JSONDecodeError:
                prefixes = {}

        # ৩. নতুন প্রিফিক্স সেট করা
        prefixes[str(interaction.guild.id)] = new_prefix

        # ৪. ফাইল সেভ করা
        with open('prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)

        await interaction.response.send_message(f"✅ Prefix successfully updated to: `{new_prefix}`", ephemeral=False)

async def setup(bot):
    await bot.add_cog(PrefixSystem(bot))
