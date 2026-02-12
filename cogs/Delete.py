import discord
from discord.ext import commands
from discord import app_commands
import asyncio
# Importing premium logic and theme colors from utils
from utils import load_config, get_theme_color

# --- 1. Confirmation View (Button Logic) ---
class ServerWipeConfirm(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(label="YES, WIPE EVERYTHING", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if the user clicking is the original author
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ This action is not authorized for you!", ephemeral=True)

        guild = interaction.guild
        await interaction.response.send_message("🚀 **Initiating full server wipe... please stand by.**", ephemeral=True)

        # 1. Delete all channels
        for channel in guild.channels:
            try:
                await channel.delete(reason="Emergency Server Wipe - Premium Command")
            except:
                continue 

        # 2. Create a fresh secure channel and send final status
        new_channel = await guild.create_text_channel(name="☢️-server-nuked")
        
        # Premium servers will use Gold theme color
        color = get_theme_color(guild.id) 
        embed = discord.Embed(
            title="🛑 SERVER SECURED & NUKED",
            description=(
                "### ────────────────────\n"
                "**The entire server has been wiped successfully.**\n"
                "```All channels and categories were removed for security reasons.```\n"
                "────────────────────"
            ),
            color=color
        )
        embed.set_footer(text="Emergency System | Security Level: Maximum")
        await new_channel.send(embed=embed)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Permission denied!", ephemeral=True)
            
        await interaction.response.edit_message(content="✅ **Emergency wipe has been cancelled.**", embed=None, view=None)
        self.stop()

# --- 2. Main Security Class ---
class ServerSecurity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium(self, guild_id):
        """Checks if the server has Premium status"""
        return get_theme_color(guild_id) == discord.Color.gold()

    @app_commands.command(name="emergency_wipe", description="🚨 [PREMIUM ONLY] Delete ALL channels for security")
    @app_commands.checks.has_permissions(administrator=True)
    async def emergency_wipe(self, interaction: discord.Interaction):
        # 1. Administrator/Owner validation
        if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ This tool is restricted to the **Server Owner** or **Administrators**.", ephemeral=True)

        # 2. Premium validation
        if not self.is_premium(interaction.guild.id):
            embed = discord.Embed(
                title="🔒 Feature Locked",
                description="This is a highly sensitive feature available only for **Premium Servers**.\n\n⭐ Unlock now using `/buy_premium`.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # 3. Stylish confirmation embed (Falcon/Nova Style)
        confirm_embed = discord.Embed(
            title="🚨 EXTREME DANGER ALERT 🚨",
            description=(
                "### Are you absolutely sure?\n"
                "────────────────────\n"
                "You are about to **DELETE EVERY CHANNEL** in this server.\n"
                "• This action is **IRREVERSIBLE**.\n"
                "• It will result in permanent data loss (Channels/Categories).\n"
                "────────────────────\n"
                "**Click the button below to execute.**"
            ),
            color=discord.Color.dark_red()
        )
        confirm_embed.set_footer(text="Authorized Administrator Request")
        
        view = ServerWipeConfirm(interaction.user.id)
        await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerSecurity(bot))
