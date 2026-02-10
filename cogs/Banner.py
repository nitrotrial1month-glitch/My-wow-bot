import discord
from discord.ext import commands
from discord import app_commands

class Banner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="banner", 
        aliases=["bn"], 
        description="ইউজার বা নিজের প্রোফাইল ব্যানার দেখুন"
    )
    async def banner(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        
        # ইউজারকে 'fetch' করা বাধ্যতামূলক কারণ ব্যানার ডাটা সাধারণ মেম্বার অবজেক্টে থাকে না
        try:
            user = await self.bot.fetch_user(member.id)
        except Exception as e:
            return await ctx.send(f"❌ ইউজার ডাটা ফেচ করতে সমস্যা হয়েছে: `{e}`")

        if not user.banner:
            # যদি প্রোফাইল ব্যানার না থাকে, তবে তার 'Banner Color' দেখানোর চেষ্টা করবে
            if user.accent_color:
                embed = discord.Embed(
                    description=f"❌ **{member.display_name}**-এর কোনো ইমেজ ব্যানার নেই, তবে একটি ব্যানার কালার আছে।",
                    color=user.accent_color
                )
                return await ctx.send(embed=embed)
            else:
                return await ctx.send(f"❌ **{member.display_name}**-এর কোনো প্রোফাইল ব্যানার বা কালার নেই।")

        # ব্যানার এমবেড ডিজাইন
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Banner",
            color=user.accent_color or 0x2b2d31
        )
        
        # ব্যানারের ইউআরএল সেট করা
        embed.set_image(url=user.banner.url)
        
        # ডাউনলোড লিঙ্ক
        embed.description = f"[Download Banner]({user.banner.url})"
        
        embed.set_footer(
            text=f"Requested by {ctx.author.name}", 
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Banner(bot))
