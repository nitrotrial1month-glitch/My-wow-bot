import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timezone
# Importing premium logic and theme colors
from utils import load_config, get_theme_color

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
        if not invites_before: return
        
        try:
            invites_after = await member.guild.invites()
            for invite in invites_before:
                for new_invite in invites_after:
                    if invite.code == new_invite.code and new_invite.uses > invite.uses:
                        data = load_data(INVITE_DB)
                        mapping = load_data(MEMBER_MAP)
                        gid, inviter_id = str(member.guild.id), str(invite.inviter.id)
                        mid = str(member.id)
                        
                        if gid not in data: data[gid] = {}
                        if inviter_id not in data[gid]:
                            data[gid][inviter_id] = {"total": 0, "left": 0, "fake": 0, "bonus": 0, "rejoin": 0}
                        
                        # Rejoin Check
                        if gid in mapping and mid in mapping[gid]:
                            data[gid][inviter_id]["rejoin"] += 1
                        else:
                            # Fake Check (Account younger than 7 days)
                            diff = datetime.now(timezone.utc) - member.created_at
                            if diff.days < 7:
                                data[gid][inviter_id]["fake"] += 1
                            
                            data[gid][inviter_id]["total"] += 1
                            if gid not in mapping: mapping[gid] = {}
                            mapping[gid][mid] = inviter_id
                        
                        save_data(INVITE_DB, data)
                        save_data(MEMBER_MAP, mapping)
                        self.invites_cache[member.guild.id] = invites_after
                        return
        except: pass

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

    @commands.hybrid_command(name="invites", aliases=["i"], description="Check detailed invite analytics")
    @app_commands.describe(member="The member whose invites you want to check")
    async def invite_check(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        data = load_data(INVITE_DB)
        gid, uid = str(ctx.guild.id), str(target.id)
        
        # Premium and Theme Logic
        color = get_theme_color(ctx.guild.id)
        is_prem = (color == discord.Color.gold())
        
        # Stats Retrieval
        stats = data.get(gid, {}).get(uid, {"total": 0, "left": 0, "fake": 0, "bonus": 0, "rejoin": 0})
        total = stats["total"] + stats["bonus"]
        valid = (stats["total"] - stats["left"] - stats["fake"]) + stats["bonus"]
        if valid < 0: valid = 0

        # Emojis
        static_arrow = "<:arrow:1467198187470196974>"
        animated_arrow = "<a:arrow:1468223732546932910>"
        dot = "<a:dot:1433392100451549234>"
        
        # Pro Design Layout (Nova/Falcon Style)
        status_text = "Premium Tracking" if is_prem else "Standard Tracking"
        
        description = (
            f"### 📩 {target.display_name}'s Invite Stats\n"
            f"────────────────────\n"
            f"{dot} **Tracking Status:** {status_text}\n"
            f"{dot} **Total Registered:** `{total}`\n\n"
            f"### {animated_arrow} Activity Details\n"
            f"{static_arrow} **Joins:** `{stats['total']}`\n"
            f"{static_arrow} **Left:** `{stats['left']}`\n"
            f"{static_arrow} **Fake:** `{stats['fake']}`\n"
            f"{static_arrow} **Bonus:** `{stats['bonus']}`\n"
            f"{static_arrow} **Rejoin:** `{stats['rejoin']}`\n"
            f"────────────────────\n"
            f"### {animated_arrow} **Final Valid Invites: `{valid}`**\n"
            f"────────────────────"
        )

        embed = discord.Embed(description=description, color=color)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Footer formatting
        embed.set_footer(text=f"Requested by {ctx.author.name} | Today at {datetime.now().strftime('%I:%M %p')}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))
                            
