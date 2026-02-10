import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# --- Global Database Path ---
DB_FILE = 'economy.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_cash = "<:Nova:1453460518764548186>"

    # এখানে আপনার বলা সবকটি নাম (Aliases) যোগ করা হয়েছে
    @commands.hybrid_command(
        name="bal", 
        aliases=["balance", "cash", "c", "Cash", "C", "money", "M", "Money", "m"], 
        description="Check global coin balance!"
    )
    @app_commands.describe(member="The member whose balance you want to check")
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        user_id = str(target.id)
        
        data = load_json(DB_FILE)
        user_data = data.get(user_id, {})
        
        balance = user_data.get("balance", 0)
        streak = user_data.get("streak", 0)

        # --- Premium Style Embed ---
        embed = discord.Embed(
            title="💳 Global Financial Status",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_author(name=f"{target.name}'s Profile", icon_url=target.display_avatar.url)
        
        embed.add_field(
            name="✨ Wallet Balance", 
            value=f"### {self.emoji_cash} **{balance:,}**", 
            inline=False
        )
        
        embed.add_field(name="🔥 Streak", value=f"`{streak} Days`", inline=True)
        
        status = "Wealthy" if balance > 100000 else "Global Citizen"
        embed.add_field(name="🏆 Rank Status", value=f"`{status}`", inline=True)
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Balance(bot))
