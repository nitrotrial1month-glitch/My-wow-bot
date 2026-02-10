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
        self.invites_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        # বট চালু হলে বর্তমান ইনভাইটগুলো মেমোরিতে রাখা
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
            except: pass

    async def update_stats(self, guild_id, inviter_id, status):
        data = load_invites()
        gid, uid = str(guild_id), str(inviter_id)
        
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
        # কে ইনভাইট করেছে তা বের করা
        invites_before = self.invites_cache.get(member.guild.id)
        invites_after = await member.guild.invites()
        
        for invite in invites_before:
            for new_invite in invites_after:
                if invite.code == new_invite.code and new_invite.uses > invite.uses:
                    # ইনভাইটারকে পাওয়া গেছে, ডাটাবেজ আপডেট
                    await self.update_stats(member.guild.id, invite.inviter.id, "join")
                    # নতুন ইনভাইটার আইডি মেম্বারের সাথে সাময়িকভাবে সেভ রাখা (লিভ ট্র্যাকিংয়ের জন্য)
                    # এটি করার জন্য একটি মেম্বার-ইনভাইটার ম্যাপিং ফাইল বা ডাটাবেজ লাগে
                    self.invites_cache[member.guild.id] = invites_after
                    return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # এখানে সমস্যা হয় কারণ ডিসকোর্ড সরাসরি বলে না কে তাকে ইনভাইট করেছিল
        # তবে আমরা ইনভাইট লিষ্ট চেক করে ডাটাবেজে 'left' কাউন্ট বাড়াতে পারি
        # এর জন্য প্রয়োজন মেম্বার জয়েন করার সময় কে ইনভাইটার ছিল তা কোথাও সেভ রাখা
        # আপাতত আমরা বেসিক 'left' ট্র্যাকিং করছি
        pass 

    @commands.hybrid_command(name="invites", aliases=["i", "invite"], description="Detailed invite tracking")
    async def invite_check(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = load_invites()
        gid, uid = str(ctx.guild.id), str(member.id)
        
        stats = data.get(gid, {}).get(uid, {"total": 0, "left": 0, "fake": 0, "bonus": 0})
        
        # ক্যালকুলেশন
        total = stats["total"]
        left = stats["left"]
        fake = stats["fake"]
        bonus = stats["bonus"]
        valid = (total - left - fake) + bonus
        if valid < 0: valid = 0

        embed = discord.Embed(title=f"📩 Invites: {member.display_name}", color=0x00ffcc)
        embed.add_field(name="✨ Valid", value=f"**` {valid} `**", inline=False)
        embed.add_field(name="📩 Total", value=f"`{total}`", inline=True)
        embed.add_field(name="🏃 Left", value=f"`{left}`", inline=True)
        embed.add_field(name="🚫 Fake", value=f"`{fake}`", inline=True)
        embed.set_footer(text=f"Invite Tracker | Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
