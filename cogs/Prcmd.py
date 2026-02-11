import discord
from discord.ext import commands
from discord import app_commands
import datetime
from utils import load_config # config.json থেকে ডাটা চেক করার জন্য

# প্রিমিয়াম চেক করার সহজ ফাংশন
def is_premium(user_id):
    config = load_config()
    premium_data = config.get("premium", {})
    if str(user_id) in premium_data:
        expiry = datetime.datetime.fromisoformat(premium_data[str(user_id)])
        return datetime.datetime.now() < expiry
    return False

class PremiumCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. প্রিমিয়াম ডেইলি (Economy Boost) ---
    @app_commands.command(name="p_daily", description="[BASIC PREMIUM] Get 5x more daily coins")
    async def p_daily(self, interaction: discord.Interaction):
        if not is_premium(interaction.user.id):
            return await interaction.response.send_message("❌ This is for **Basic Premium** members only!", ephemeral=True)
        
        # এখানে আপনার ইকোনমি সিস্টেমের সাথে কানেক্ট করতে পারেন
        amount = 5000 # সাধারণ ইউজার ১০০০ পেলে এরা ৫০০০ পাবে
        await interaction.response.send_message(f"💰 **Premium Daily:** You received `{amount}` coins! (5x Bonus applied)")

    # --- ২. ভিআইপি সায় (Identity) ---
    @app_commands.command(name="p_say", description="[BASIC PREMIUM] Make the bot speak in a stylish embed")
    async def p_say(self, interaction: discord.Interaction, message: str):
        if not is_premium(interaction.user.id):
            return await interaction.response.send_message("⭐ Upgrade to Premium to use VIP Say!", ephemeral=True)

        embed = discord.Embed(
            description=message,
            color=discord.Color.from_rgb(255, 215, 0) # Gold Color
        )
        embed.set_author(name=f"{interaction.user.display_name} says:", icon_url=interaction.user.avatar.url)
        embed.set_footer(text="Premium Member Exclusive")
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Sent!", ephemeral=True)

    # --- ৩. অ্যাডভান্সড ইউজার ইনফো (Utility) ---
    @app_commands.command(name="p_userinfo", description="[BASIC PREMIUM] Get detailed info about a user")
    async def p_userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        if not is_premium(interaction.user.id):
            return await interaction.response.send_message("❌ Premium required for detailed user audits.", ephemeral=True)

        member = member or interaction.user
        roles = [role.mention for role in member.roles[1:]] # @everyone বাদ দিয়ে
        
        embed = discord.Embed(title=f"User Audit: {member.name}", color=member.color)
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Joined Discord", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Roles", value=" ".join(roles) if roles else "None", inline=False)
        embed.set_footer(text="Powered by WOW Premium")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumCmds(bot))
      
