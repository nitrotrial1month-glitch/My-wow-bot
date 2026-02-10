import discord
from discord.ext import commands
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
        self.invites = {} # ইনভাইট কোড ক্যাশ করার জন্য

    @commands.Cog.listener()
    async def on_ready(self):
        # বট চালু হওয়ার সময় সব ইনভাইট কোড সেভ করে রাখা
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except: pass

    async def update_invite_db(self, inviter_id, guild_id, status):
        data = load_invites()
        gid = str(guild_id)
        uid = str(inviter_id)
        
        if gid not in data: data[gid] = {}
        if uid not in data[gid]: 
            data[gid][uid] = {"total": 0, "left": 0, "fake": 0, "bonus": 0}
        
        if status == "join":
            data[gid][uid]["total"] += 1
        elif status == "left":
            data[gid][uid]["left"] += 1
            
        save_invites(data)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        invites_before = self.invites.get(member.guild.id)
        invites_after = await member.guild.invites()
        
        for invite in invites_before:
            for new_invite in invites_after:
                if invite.code == new_invite.code and new_invite.uses > invite.uses:
                    # ইনভাইটারকে খুঁজে পাওয়া গেছে
                    await self.update_invite_db(invite.inviter.id, member.guild.id, "join")
                    self.invites[member.guild.id] = invites_after
                    return

    @commands.hybrid_command(name="invites", description="Advanced Invite Information")
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
            color=0x00ffcc, # ফ্যালকনের চেয়েও উজ্জ্বল কালার
            description=f"Detailed invite tracking for {member.mention}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # ইনফরমেশন কার্ডস
        embed.add_field(name="📩 Total", value=f"`{total}`", inline=True)
        embed.add_field(name="✅ Regular", value=f"`{regular}`", inline=True)
        embed.add_field(name="🏃 Left", value=f"`{stats['left']}`", inline=True)
        embed.add_field(name="🚫 Fake", value=f"`{stats['fake']}`", inline=True)
        embed.add_field(name="🎁 Bonus", value=f"`{stats['bonus']}`", inline=True)
        
        # প্রগ্রেস বার স্টাইল (ফ্যালকন থেকে ভালো দেখাবে)
        embed.add_field(name="📈 Progress", value=f"You have `{regular}` valid invites.", inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
      
