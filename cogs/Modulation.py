import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. মেসেজ ক্লিয়ার (Clear/Purge) ---
    @app_commands.command(name="clear", description="নির্দিষ্ট সংখ্যক মেসেজ ডিলিট করার জন্য")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ সফলভাবে `{len(deleted)}` টি মেসেজ ডিলিট করা হয়েছে।")

    # --- ২. ব্যান (Ban) ---
    @app_commands.command(name="ban", description="কাউকে সার্ভার থেকে ব্যান করার জন্য")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "কোনো কারণ দেওয়া হয়নি"):
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"🔨 **{member.name}** কে ব্যান করা হয়েছে।\n**কারণ:** {reason}")
        except:
            await interaction.response.send_message("❌ ব্যান করতে ব্যর্থ হয়েছি। পারমিশন চেক করুন।", ephemeral=True)

    # --- ৩. আনব্যান (Unban) ---
    @app_commands.command(name="unban", description="কাউকে আনব্যান করার জন্য")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        await interaction.response.defer()
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.followup.send(f"✅ **{user.name}** কে সফলভাবে আনব্যান করা হয়েছে।")
        except:
            await interaction.followup.send("❌ এই আইডিটি ব্যান লিস্টে পাওয়া যায়নি বা ভুল আইডি।")

    # --- ৪. টাইম-আউট/মিউট (Mute/Timeout) ---
    @app_commands.command(name="timeout", description="কাউকে নির্দিষ্ট সময়ের জন্য মিউট করার জন্য")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "কোনো কারণ দেওয়া হয়নি"):
        duration = datetime.timedelta(minutes=minutes)
        try:
            await member.timeout(duration, reason=reason)
            await interaction.response.send_message(f"🔇 **{member.name}** কে {minutes} মিনিটের জন্য মিউট করা হয়েছে।\n**কারণ:** {reason}")
        except:
            await interaction.response.send_message("❌ টাইম-আউট দিতে ব্যর্থ হয়েছি।", ephemeral=True)

    # --- ৫. লক চ্যানেল (Lock) ---
    @app_commands.command(name="lock", description="বর্তমান চ্যানেলটি লক করার জন্য")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"🔒 {interaction.channel.mention} সফলভাবে লক করা হয়েছে।")

    # --- ৬. আনলক চ্যানেল (Unlock) ---
    @app_commands.command(name="unlock", description="লক করা চ্যানেল আনলক করার জন্য")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(f"🔓 {interaction.channel.mention} এখন সবার জন্য উন্মুক্ত।")

    # --- ৭. কিক (Kick) ---
    @app_commands.command(name="kick", description="কাউকে সার্ভার থেকে কিক করার জন্য")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "কোনো কারণ দেওয়া হয়নি"):
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"👞 **{member.name}** কে কিক করা হয়েছে।\n**কারণ:** {reason}")
        except:
            await interaction.response.send_message("❌ কিক করতে ব্যর্থ হয়েছি।", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
                    
