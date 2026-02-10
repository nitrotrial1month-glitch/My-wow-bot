import discord
from discord.ext import commands
from discord import app_commands

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="avatar", 
        aliases=["av", "pfp"], 
        description="ইউজার বা নিজের প্রোফাইল পিকচার দেখুন"
    )
    @app_commands.describe(member="যার অবতার দেখতে চান তাকে সিলেক্ট করুন")
    async def avatar(self, ctx, member: discord.Member = None):
        # যদি কেউ মেনশন না করে তবে নিজের অবতার দেখাবে
        member = member or ctx.author
        
        # ইউজার অবতারের ইউআরএল
        avatar_url = member.display_avatar.url
        
        # এমবেড ডিজাইন
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=0x2b2d31
        )
        
        # বিভিন্ন ফরম্যাটে ডাউনলোড করার লিঙ্ক (ফুটারে বা ডেসক্রিপশনে দেওয়া যায়)
        embed.description = f"[PNG]({member.display_avatar.with_format('png')}) | [JPG]({member.display_avatar.with_format('jpg')}) | [WebP]({member.display_avatar.with_format('webp')})"
        
        # মেইন ইমেজ সেট করা
        embed.set_image(url=avatar_url)
        
        # আপনার সেই ইমোজিগুলো চাইলে ফুটারে ইউজ করতে পারেন
        animated_arrow = "<a:arrow:1468223732546932910>"
        embed.set_footer(
            text=f"Requested by {ctx.author.name}", 
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Avatar(bot))
  
