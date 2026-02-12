import discord
from discord.ext import commands
from discord import app_commands
import asyncio
# utils থেকে প্রিমিয়াম লজিক এবং থিম কালার ইমপোর্ট
from utils import load_config, get_theme_color

# --- ১. কনফার্মেশন ভিউ (বাটন লজিক) ---
class ServerWipeConfirm(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(label="YES, WIPE EVERYTHING", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # বাটন ক্লিক করা ইউজার পোল হোস্ট কি না চেক
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ এটি আপনার জন্য নয়!", ephemeral=True)

        guild = interaction.guild
        await interaction.response.send_message("🚀 **বড় ধরনের ধ্বংসযজ্ঞ শুরু হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন।**", ephemeral=True)

        # ১. সব চ্যানেল ডিলিট করা (বট যে চ্যানেলে আছে সেটি বাদে সব)
        for channel in guild.channels:
            try:
                await channel.delete(reason="Emergency Server Wipe - Premium Command")
            except:
                continue 

        # ২. নতুন একটি চ্যানেল তৈরি করা এবং মেসেজ দেওয়া
        new_channel = await guild.create_text_channel(name="☢️-server-nuked")
        
        color = get_theme_color(guild.id) # প্রিমিয়াম সার্ভার হলে Gold কালার
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
        embed.set_footer(text="Emergency System | Security Level: Max")
        await new_channel.send(embed=embed)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ অনুমতি নেই!", ephemeral=True)
            
        await interaction.response.edit_message(content="✅ **Emergency wipe বাতিল করা হয়েছে।**", embed=None, view=None)
        self.stop()

# --- ২. মেইন সিকিউরিটি ক্লাস ---
class ServerSecurity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium(self, guild_id):
        """সার্ভার প্রিমিয়াম কি না চেক করবে"""
        return get_theme_color(guild_id) == discord.Color.gold()

    @app_commands.command(name="emergency_wipe", description="🚨 [PREMIUM ONLY] Delete ALL channels for security")
    @app_commands.checks.has_permissions(administrator=True)
    async def emergency_wipe(self, interaction: discord.Interaction):
        # ১. অ্যাডমিন বা ওনার চেক
        if not interaction.user.guild_permissions.administrator and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ এটি শুধুমাত্র **Server Owner** বা **Administrators** ব্যবহার করতে পারবে।", ephemeral=True)

        # ২. প্রিমিয়াম চেক
        if not self.is_premium(interaction.guild.id):
            embed = discord.Embed(
                title="🔒 Feature Locked",
                description="এটি একটি অত্যন্ত সংবেদনশীল ফিচার যা শুধুমাত্র **Premium Server**-এ উপলব্ধ।\n\n⭐ আনলক করতে `/buy_premium` ব্যবহার করুন।",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ৩. স্টাইলিশ কনফার্মেশন এমবেড (Falcon/Nova Style)
        confirm_embed = discord.Embed(
            title="🚨 EXTREME DANGER ALERT 🚨",
            description=(
                "### আপনি কি নিশ্চিত?\n"
                "────────────────────\n"
                "আপনি এই সার্ভারের **প্রতিটি চ্যানেল এবং ক্যাটাগরি** ডিলিট করতে যাচ্ছেন।\n"
                "• এই কাজটি একবার করলে আর **ফেরানো সম্ভব নয়**।\n"
                "• এটি একটি স্থায়ী ধ্বংসযজ্ঞ (Permanent Destruction)।\n"
                "────────────────────\n"
                "**প্রক্রিয়াটি চালিয়ে যেতে নিচের বাটনে ক্লিক করুন।**"
            ),
            color=discord.Color.dark_red()
        )
        confirm_embed.set_footer(text="Requested by Authorized Administrator")
        
        view = ServerWipeConfirm(interaction.user.id)
        await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerSecurity(bot))
