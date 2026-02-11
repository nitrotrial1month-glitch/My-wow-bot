import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils import check_advanced_premium

# --- টিয়ার লেভেল কনফিগারেশন ---
TIER_LEVELS = {
    "free": 0,
    "basic": 1,
    "pro": 2,
    "ultra": 3
}

# --- কনফার্মেশন বাটন ভিউ ---
class NukeConfirmView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=30)
        self.author_id = author_id

    @discord.ui.button(label="Confirm Nuke", style=discord.ButtonStyle.danger, emoji="☢️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # শুধুমাত্র কমান্ড দাতা বাটন চাপতে পারবে
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ This is not your button!", ephemeral=True)

        channel = interaction.channel
        
        # ১. চ্যানেলের পজিশন সেভ করা
        position = channel.position
        
        # ২. চ্যানেল ক্লোন করা (একই পারমিশনসহ নতুন চ্যানেল)
        new_channel = await channel.clone(reason=f"Nuked by {interaction.user}")
        
        # ৩. পুরনো চ্যানেল ডিলিট করা
        await channel.delete()
        
        # ৪. নতুন চ্যানেলকে সঠিক পজিশনে রাখা
        await new_channel.edit(position=position)

        # ৫. নতুন চ্যানেলে নুকে ইফেক্ট মেসেজ পাঠানো
        embed = discord.Embed(
            title="☢️ Channel Nuked!",
            description=f"This channel has been reset by {interaction.user.mention}.",
            color=discord.Color.red()
        )
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMjhiazRycjRwaXp6bmR6Z3Z4bmR6Z3Z4bmR6Z3Z4bmR6Z3Z4JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/HhTXt43pk1I1W/giphy.gif")
        
        await new_channel.send(embed=embed)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not your button!", ephemeral=True)
            
        await interaction.response.edit_message(content="❌ Nuke cancelled.", embed=None, view=None)
        self.stop()

class NukeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="nuke", description="☢️ [PRO/ULTRA] Recreate the channel to clear all messages")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nuke(self, ctx):
        # --- প্রিমিয়াম চেক লজিক ---
        user_data = check_advanced_premium(ctx.author.id)
        server_data = check_advanced_premium(None, ctx.guild.id)
        
        user_lvl = TIER_LEVELS.get(user_data["tier"], 0) if user_data["active"] else 0
        server_lvl = TIER_LEVELS.get(server_data["tier"], 0) if server_data["active"] else 0
        
        # প্রিমিয়াম লেভেল অন্তত 'Pro' (২) বা তার উপরে হতে হবে
        if max(user_lvl, server_lvl) < 2:
            embed = discord.Embed(
                title="💎 Premium Feature",
                description="The **Nuke** command is only available for **Pro** and **Ultra** members.\n\n"
                            "🥉 Basic: ❌\n🥈 **Pro: ✅**\n🥇 **Ultra: ✅**",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        # --- কনফার্মেশন চাওয়া ---
        confirm_embed = discord.Embed(
            title="⚠️ Warning!",
            description="Are you sure you want to **NUKE** this channel?\n"
                        "This will delete **ALL** message history and recreate the channel.",
            color=discord.Color.dark_red()
        )
        
        view = NukeConfirmView(ctx.author.id)
        await ctx.send(embed=confirm_embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(NukeCommand(bot))
  
