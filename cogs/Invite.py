import discord
from discord.ext import commands
from discord import app_commands
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

    @commands.hybrid_command(
        name="invites", 
        aliases=["i", "invite"], 
        description="Check detailed and valid invite statistics"
    )
    async def invite_check(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = load_invites()
        gid, uid = str(ctx.guild.id), str(member.id)
        
        # ডাটাবেজ থেকে তথ্য নেওয়া
        stats = data.get(gid, {}).get(uid, {"total": 0, "left": 0, "fake": 0, "bonus": 0})
        
        # ক্যালকুলেশন (Valid = Total - Left - Fake + Bonus)
        total_joins = stats["total"]
        left_members = stats["left"]
        fake_invites = stats["fake"]
        bonus_invites = stats["bonus"]
        
        # ভ্যালিড ইনভাইট বের করার আসল সূত্র
        valid_invites = (total_joins - left_members - fake_invites) + bonus_invites
        if valid_invites < 0: valid_invites = 0 # যেন মাইনাস না দেখায়

        embed = discord.Embed(
            title=f"📊 Invite Stats: {member.display_name}",
            color=0x2f3136, # প্রিমিয়াম ডার্ক কালার
            description=f"Showing invite analytics for {member.mention}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # মূল ভ্যালিড ইনভাইট সবার উপরে বড় করে দেখানো
        embed.add_field(name="✨ Valid Invites", value=f"**` {valid_invites} `**", inline=False)
        
        # অন্যান্য ডিটেইলস
        embed.add_field(name="📩 Total Joins", value=f"`{total_joins}`", inline=True)
        embed.add_field(name="🏃 Left", value=f"`{left_members}`", inline=True)
        embed.add_field(name="🚫 Fake", value=f"`{fake_invites}`", inline=True)
        embed.add_field(name="🎁 Bonus", value=f"`{bonus_invites}`", inline=True)
        
        # ড্যাশবোর্ড স্টাইল স্ট্যাটাস লাইন
        embed.add_field(
            name="📝 Summary", 
            value=f"You currently have **{valid_invites}** active invites on this server.", 
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
