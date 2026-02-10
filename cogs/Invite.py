import discord
from discord.ext import commands
from discord import app_commands
import json
import os

INVITE_DB = 'invites.json'
MEMBER_MAP = 'member_map.json' # কে কার মাধ্যমে জয়েন করেছে তা সেভ রাখার জন্য

# --- ডাটাবেজ ফাংশন ---
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
        # বট অন হলে সব ইনভাইট ক্যাশ করা
        for guild in self.bot.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
            except: pass

    # --- ইনভাইট ট্র্যাকিং লজিক ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        invites_before = self.invites_cache.get(member.guild.id)
        invites_after = await member.guild.invites()
        
        for invite in invites_before:
            for new_invite in invites_after:
                if invite.code == new_invite.code and new_invite.uses > invite.uses:
                    # ১. ইনভাইটার ডাটা আপডেট
                    data = load_data(INVITE_DB)
                    gid, inviter_id = str(member.guild.id), str(invite.inviter.id)
                    
                    if gid not in data: data[gid] = {}
                    if inviter_id not in data[gid]:
                        data[gid][inviter_id] = {"total": 0, "left": 0, "fake": 0, "bonus": 0}
                    
                    data[gid][inviter_id]["total"] += 1
                    save_data(INVITE_DB, data)
                    
                    # ২. মেম্বার ম্যাপিং (লিভ ট্র্যাকিংয়ের জন্য জরুরি)
                    mapping = load_data(MEMBER_MAP)
                    if gid not in mapping: mapping[gid] = {}
                    mapping[gid][str(member.id)] = inviter_id
                    save_data(MEMBER_MAP, mapping)
                    
                    self.invites_cache[member.guild.id] = invites_after
                    return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # কেউ লিভ নিলে তাকে কে ইনভাইট করেছিল তা খুঁজে বের করা
        mapping = load_data(MEMBER_MAP)
        gid = str(member.guild.id)
        mid = str(member.id)
        
        if gid in mapping and mid in mapping[gid]:
            inviter_id = mapping[gid][mid]
            data = load_data(INVITE_DB)
            
            if gid in data and inviter_id in data[gid]:
                data[gid][inviter_id]["left"] += 1
                save_data(INVITE_DB, data)
                
                # লিস্ট থেকে মেম্বারকে রিমুভ করা
                del mapping[gid][mid]
                save_data(MEMBER_MAP, mapping)

    # --- কমান্ড সেকশন (Wow i / Wow invites / Slash) ---
    @commands.hybrid_command(
        name="invites", 
        aliases=["i", "inv"], 
        description="Check detailed and valid invite statistics"
    )
    @app_commands.describe(member="Select a member to check their invites")
    async def invite_check(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = load_data(INVITE_DB)
        gid, uid = str(ctx.guild.id), str(member.id)
        
        stats = data.get(gid, {}).get(uid, {"total": 0, "left": 0, "fake": 0, "bonus": 0})
        
        # ক্যালকুলেশন
        total = stats["total"]
        left = stats["left"]
        fake = stats["fake"]
        bonus = stats["bonus"]
        valid = (total - left - fake) + bonus
        if valid < 0: valid = 0

        embed = discord.Embed(
            title=f"📊 Invite Stats: {member.display_name}",
            color=0x00ffcc,
            description=f"Invite information for {member.mention}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # তথ্যগুলো সাজানো
        embed.add_field(name="✨ Valid Invites", value=f"**` {valid} `**", inline=False)
        embed.add_field(name="📩 Total Joins", value=f"`{total}`", inline=True)
        embed.add_field(name="🏃 Left Members", value=f"`{left}`", inline=True)
        embed.add_field(name="🚫 Fake/Bots", value=f"`{fake}`", inline=True)
        embed.add_field(name="🎁 Bonus", value=f"`{bonus}`", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
    
