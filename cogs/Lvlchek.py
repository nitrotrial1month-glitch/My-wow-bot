    # --- LEVEL CHECK COMMAND ---
    # name="lvl" দেওয়ার ফলে স্ল্যাশ কমান্ড হবে /lvl
    # aliases=["exp","xp","EXP","Exp","XP","Xp", "level"] দেওয়ার ফলে প্রিফিক্স হবে !rank, !level
    @commands.hybrid_command(name="lvl", description="📊 Check your current global level", aliases=["rank", "level"])
    async def lvl(self, ctx, member: discord.Member = None):
        user = member or ctx.author
        uid = str(user.id)
        data = load_json(LEVEL_FILE)

        # যদি ডাটা না থাকে
        if uid not in data:
            embed = discord.Embed(description=f"🚫 **{user.display_name}** has not earned any XP yet!", color=discord.Color.red())
            return await ctx.send(embed=embed)

        lvl_num = data[uid]["level"]
        xp = data[uid]["xp"]
        
        # পরবর্তী লেভেলের জন্য কত XP লাগবে
        needed = self.get_xp_needed(lvl_num)

        # --- Stylish Progress Bar ---
        # 40% পূর্ণ হলে দেখাবে: 🟦🟦🟦🟦⬜⬜⬜⬜⬜⬜
        percent = min(100, int((xp / needed) * 100))
        bar_length = 12
        filled = int(bar_length * percent / 100)
        
        if filled == bar_length:
            bar = "🟩" * filled # পূর্ণ হলে সবুজ
        else:
            bar = "🟦" * filled + "⬜" * (bar_length - filled)

        # --- Rank Card Embed ---
        embed = discord.Embed(
            title=f"📊 Global Rank Card",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        
        # সুন্দর কোড ব্লক ডিজাইন
        embed.add_field(name="🔰 Level", value=f"```\n{lvl_num}\n```", inline=True)
        embed.add_field(name="✨ XP Earned", value=f"```\n{xp} / {needed}\n```", inline=True)
        
        # প্রোগ্রেস বার
        embed.add_field(name=f"🚀 Progress ({percent}%)", value=f"`{bar}`", inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)
      
