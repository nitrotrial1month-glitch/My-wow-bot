import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import os
import datetime

# Database Files
DB_FILE = 'economy.json'
CONFIG_FILE = 'daily_config.json'

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Daily Image Dashboard Modal ---
class DailyDashboardModal(Modal, title="Daily Command Dashboard"):
    img_input = TextInput(
        label="Main Image/GIF URL", 
        placeholder="https://example.com/reward.gif",
        required=False
    )
    thumb_input = TextInput(
        label="Thumbnail URL (Optional)", 
        placeholder="https://example.com/icon.png",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_json(CONFIG_FILE)
        config['image_url'] = self.img_input.value if self.img_input.value else "https://i.imgur.com/8NID0vH.gif"
        config['thumb_url'] = self.thumb_input.value if self.thumb_input.value else None
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message("✅ Daily Command Dashboard updated successfully!", ephemeral=True)

class DailyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Dashboard Command
    @app_commands.command(name="daily_dashboard", description="Set the image and thumbnail for the daily reward")
    @app_commands.checks.has_permissions(administrator=True)
    async def daily_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(DailyDashboardModal())

    async def process_daily(self, ctx_or_interaction, user):
        data = load_data() # From previous setup
        config = load_json(CONFIG_FILE)
        
        # Default fallback image
        image_url = config.get('image_url', "https://i.imgur.com/8NID0vH.gif")
        thumb_url = config.get('thumb_url', user.display_avatar.url)

        # ... (Previous balance and streak logic here) ...
        # (Assuming variables 'reward', 'streak', and 'balance' are calculated as before)

        embed = discord.Embed(
            title="✨ DAILY REWARD CLAIMED ✨",
            description=f"Congratulations {user.mention}!",
            color=0x2ecc71
        )
        embed.set_thumbnail(url=thumb_url)
        embed.add_field(name="💰 Earned", value=f"**{reward}** Coins", inline=True)
        embed.add_field(name="🔥 Streak", value=f"**{streak + 1}** Days", inline=True)
        embed.add_field(name="🏦 Balance", value=f"**{user_data['balance']}** Coins", inline=False)
        
        # Set the custom image from Dashboard
        embed.set_image(url=image_url)
        embed.set_footer(text="Keep your streak alive for more rewards!")

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

    @commands.command(name="daily")
    async def daily_prefix(self, ctx):
        await self.process_daily(ctx, ctx.author)

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily_slash(self, interaction: discord.Interaction):
        await self.process_daily(interaction, interaction.user)

async def setup(bot):
    await bot.add_cog(DailyCommand(bot))
