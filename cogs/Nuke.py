import discord
from discord.ext import commands
from discord import app_commands
import asyncio
# Importing premium logic and theme colors from utils
from utils import load_config, get_theme_color

# --- 1. Confirmation View (Nuke Logic) ---
class NukeConfirmView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=30)
        self.author_id = author_id

    @discord.ui.button(label="Confirm Nuke", style=discord.ButtonStyle.danger, emoji="☢️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Author validation
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ This action is not authorized for you!", ephemeral=True)

        channel = interaction.channel
        position = channel.position
        
        # Clone and Delete Logic
        try:
            new_channel = await channel.clone(reason=f"Channel Nuked by {interaction.user}")
            await channel.delete()
            await new_channel.edit(position=position)

            # Stylish Falcon Style Success Embed
            color = get_theme_color(interaction.guild.id)
            embed = discord.Embed(
                title="☢️ Channel Nuked",
                description=(
                    f"### ────────────────────\n"
                    f"**This channel has been reset successfully.**\n"
                    f"• **Executor:** {interaction.user.mention}\n"
                    f"• **Status:** Cleared & Recreated\n"
                    f"────────────────────"
                ),
                color=color
            )
            embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMjhiazRycjRwaXp6bmR6Z3Z4bmR6Z3Z4bmR6Z3Z4bmR6Z3Z4JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/HhTXt43pk1I1W/giphy.gif")
            embed.set_footer(text="Wow Security System | Channel Reset")
            
            await new_channel.send(embed=embed)
        except Exception as e:
            print(f"Nuke Error: {e}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Permission denied!", ephemeral=True)
            
        await interaction.response.edit_message(content="✅ **Nuke operation cancelled.**", embed=None, view=None)
        self.stop()

# --- 2. Main Cog ---
class NukeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium(self, guild_id):
        """Checks if the server has Premium status"""
        return get_theme_color(guild_id) == discord.Color.gold()

    @app_commands.command(name="nuke", description="☢️ [PREMIUM ONLY] Recreate the channel to clear all messages")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nuke(self, interaction: discord.Interaction):
        # 1. Premium validation
        if not self.is_premium(interaction.guild.id):
            embed = discord.Embed(
                title="🔒 Feature Locked",
                description="The **Nuke** command is exclusive to **Premium Servers**.\n\n⭐ Unlock this feature with `/buy_premium`.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # 2. Stylish Confirmation Embed (Falcon Style)
        confirm_embed = discord.Embed(
            title="☢️ NUKE AUTHORIZATION ☢️",
            description=(
                "### Are you sure?\n"
                "────────────────────\n"
                "You are about to **NUKE** this channel.\n"
                "• All message history will be **permanently deleted**.\n"
                "• The channel settings and permissions will be cloned.\n"
                "────────────────────\n"
                "**Click below to proceed.**"
            ),
            color=discord.Color.dark_red()
        )
        confirm_embed.set_footer(text="Warning: This action cannot be undone")
        
        view = NukeConfirmView(interaction.user.id)
        await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(NukeCommand(bot))
