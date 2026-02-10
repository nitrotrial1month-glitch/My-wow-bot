import discord
from discord.ext import commands
from discord import app_commands
import json
import os

INVITE_DB = 'invites.json'
MEMBER_MAP = 'member_map.json'

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return {}

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=4)

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
            except: pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        invites_before = self.invites_cache.get(member.guild.id)
        invites_after = await member.guild.invites()
        
        for invite in invites_before:
            for new_invite in invites_after:
                if invite.code == new_invite.code and new_invite.uses > invite.uses:
                    data = load_data(INVITE_DB)
                    gid, inviter_id = str(member.guild.id), str(invite.inviter.id)
                    
                    if gid not in data: data[gid] = {}
                    if inviter_id not in data[gid]:
                        data[gid][inviter_id] = {"total": 0, "left": 0, "fake": 0, "bonus": 0}
                    
                    data[gid][inviter_id]["total"] += 1
                    save_data(INVITE_DB, data)
                    
                    mapping = load_data(MEMBER_MAP)
                    if gid not in mapping: mapping[gid] = {}
                    mapping[gid][str(member.id)] = inviter_id
                    save_data(MEMBER_MAP, mapping)
                    
                    self.invites_cache[member.guild.id] = invites_after
                    return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        mapping = load_data(MEMBER_MAP)
        gid, mid = str(member.guild.id), str(member.id)
        
        if gid in mapping and mid in mapping[gid]:
            inviter_id = mapping[gid][mid]
            data = load_data(INVITE_DB)
            if gid in data and inviter_id in data[gid]:
                data[gid][inviter_id]["left"] += 1
                save_data(INVITE_DB, data)

    @commands.hybrid_command(name="invites", aliases=["i", "inv"], description="Advanced Invite Tracker")
    async def invite_check(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = load_data(INVITE_DB)
        gid, uid = str(ctx.guild.id), str(member.id)
        
        stats = data.get(gid, {}).get(uid, {"total": 0, "left": 0, "fake": 0, "bonus": 0})
        
        total = stats["total"] + stats["bonus"]
        left = stats["left"]
        fake = stats["fake"]
        bonus = stats["bonus"]
        valid = (stats["total"] - left - fake) + bonus
        if valid < 0: valid = 0

        # ডিজাইন অনুযায়ী এমবেড তৈরি
        embed = discord.Embed(
            title=f"📩 {member.display_name}'s Invites — {total}", # নামের পাশে টোটাল ইনভাইট
            color=0x2b2d31
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # মাঝখানের তথ্যগুলো
        embed.add_field(name="📥 Joins", value=f"`{stats['total']}`", inline=True)
        embed.add_field(name="📤 Left", value=f"`{left}`", inline=True)
        embed.add_field(name="🚫 Fake", value=f"`{fake}`", inline=True)
        embed.add_field(name="🎁 Bonus", value=f"`{bonus}`", inline=True)
        
        # ইউজারের রিজিয়ন (অ্যাকাউন্ট ইনফো থেকে আইডিয়া পাওয়া যায়)
        region = "Global" # ডিসকোর্ড এপিআই সরাসরি রিজিয়ন দেয় না, তাই এটি ডিফল্ট রাখা হয়েছে
        embed.add_field(name="🌍 Region", value=f"`{region}`", inline=True)
        
        # ভ্যালিড ইনভাইট সবার নিচে বড় করে
        embed.add_field(name="━━━━━━━━━━━━━━━━━━", value=f"✨ **Valid Invites:** `{valid}`", inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
    
