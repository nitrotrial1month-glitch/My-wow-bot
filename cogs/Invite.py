import discord
from discord.ext import commands
from discord import app_commands # স্ল্যাশ কমান্ডের জন্য
import json
import os

INVITE_DB = 'invites.json'

def load_invites():
    if os.path.exists(INVITE_DB):
        with open(INVITE_DB, 'r') as f: return json.load(f)
    return {}

def save_invites(data):
    with open(INVITE_DB, 'w') as f: json.dump(data, f, indent=4)

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        # বট চালু হলে ইনভাইটগুলো ক্যাশ করে রাখা
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
            except: pass

    # --- Hybrid Command: এটি টেক্সট (Wow i) এবং স্ল্যাশ (/) দুইভাবেই কাজ করবে ---
    @commands.hybrid_command(
        name="invites", 
        aliases=["i", "invite"], # এখানে 'i' যোগ করা হয়েছে যাতে 'Wow i' কাজ করে
        description="Check detailed invite statistics (Slash command supported)"
    )
    @app_commands.describe(member="The member whose invites you want to check")
    async def invite_check(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = load_invites()
        gid, uid = str(ctx.guild.id), str(member.id)
        
        stats = data.get(gid, {}).get(uid, {"total": 0, "left": 0, "fake": 0, "bonus": 0})
        
        # ক্যালকুলেশন
        regular = stats["total"] - stats["left"]
        total = stats["total"] + stats["bonus"]
        
        embed = discord.Embed(
            title=f"📊 Invite Stats: {member.display_name}",
            color=0x00ffcc,
            description=f"Detailed tracking for {member.mention}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # তথ্যগুলো সাজানো
        embed.add_field(name="📩 Total", value=f"`{total}`", inline=True)
        embed.add_field(name="✅ Regular", value=f"`{regular}`", inline=True)
        embed.add_field(name="🏃 Left", value=f"`{stats['left']}`", inline=True)
        embed.add_field(name="🚫 Fake", value=f"`{stats['fake']}`", inline=True)
        embed.add_field(name="🎁 Bonus", value=f"`{stats['bonus']}`", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
