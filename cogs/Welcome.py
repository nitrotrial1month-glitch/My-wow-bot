import discord
from discord.ext import commands
from utils import load_config, save_config

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= ইভেন্ট: যখন নতুন মেম্বার জয়েন করবে =================
    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = load_config()
        welcome_data = config.get("welcome", {})

        # ১. অন/অফ চেক (সবার আগে)
        # যদি enabled 'False' হয়, তবে ফাংশন এখানেই থামবে
        if not welcome_data.get("enabled", True): 
            return 

        # ২. অটো-রোল দেওয়া
        role_id = config.get("auto_role_id")
        if role_id:
            role = member.guild.get_role(int(role_id))
            if role:
                try: await member.add_roles(role)
                except: pass

        # ৩. ওয়েলকাম মেসেজ পাঠানো
        channel_id = welcome_data.get("channel_id")
        if channel_id:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                description = welcome_data.get("description", "Welcome {member}!").replace("{member}", member.mention)
                description = description.replace("{name}", member.name)
                description = description.replace("{server}", member.guild.name)
                description = description.replace("{count}", str(member.guild.member_count))

                embed = discord.Embed(
                    title=welcome_data.get("title", "Welcome!"),
                    description=description,
                    color=welcome_data.get("color", 0x00ff00)
                )
                
                if welcome_data.get("image_url"):
                    embed.set_image(url=welcome_data["image_url"])
                
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{member.guild.member_count}")

                try: await channel.send(content=f"Hey {member.mention}, Welcome!", embed=embed)
                except: pass

    # ================= কমান্ড গ্রুপ =================

    @commands.hybrid_group(name="setwelcome", description="Setup welcome settings")
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("❌ Usage: `toggle`, `status`, `channel`, `msg`, `image`")

    # ➤ 1. অন/অফ সুইচ (Toggle)
    @setwelcome.command(name="toggle", description="Turn welcome system ON or OFF")
    async def toggle_welcome(self, ctx, status: bool):
        config = load_config()
        # যদি 'welcome' কি (key) না থাকে তবে তৈরি করবে
        if "welcome" not in config: config["welcome"] = {}
        
        config["welcome"]["enabled"] = status
        save_config(config)
        
        state = "🟢 ON" if status else "🔴 OFF"
        await ctx.send(f"✅ Welcome System is now **{state}**")

    # ➤ 2. ড্যাশবোর্ড / স্ট্যাটাস চেক (Dashboard)
    @setwelcome.command(name="dashboard", aliases=["status", "settings"], description="View current welcome settings")
    async def show_dashboard(self, ctx):
        config = load_config()
        w = config.get("welcome", {})
        
        # ডাটা প্রিপারেশন
        is_on = "🟢 Enabled" if w.get("enabled", True) else "🔴 Disabled"
        channel = f"<#{w.get('channel_id')}>" if w.get('channel_id') else "❌ Not Set"
        role = f"<@&{config.get('auto_role_id')}>" if config.get('auto_role_id') else "❌ Not Set"
        img_status = "✅ Set" if w.get('image_url') else "❌ Not Set"

        # ড্যাশবোর্ড এমবেড
        embed = discord.Embed(title="⚙️ Welcome Settings Dashboard", color=0x2b2d31)
        embed.add_field(name="System Status", value=is_on, inline=True)
        embed.add_field(name="Channel", value=channel, inline=True)
        embed.add_field(name="Auto Role", value=role, inline=True)
        embed.add_field(name="Image", value=img_status, inline=True)
        embed.add_field(name="Message Preview", value=w.get('description', 'Default Message')[:100] + "...", inline=False)
        
        await ctx.send(embed=embed)

    # ➤ 3. অন্যান্য সেটআপ কমান্ড
    @setwelcome.command(name="channel", description="Set welcome channel")
    async def set_channel(self, ctx, channel: discord.TextChannel):
        config = load_config()
        if "welcome" not in config: config["welcome"] = {}
        config["welcome"]["channel_id"] = channel.id
        save_config(config)
        await ctx.send(f"✅ Welcome channel set to {channel.mention}")

    @setwelcome.command(name="msg", description="Set welcome message")
    async def set_msg(self, ctx, *, message: str):
        config = load_config()
        config["welcome"]["description"] = message
        save_config(config)
        await ctx.send(f"✅ Welcome message updated!")

    @setwelcome.command(name="image", description="Set welcome image URL")
    async def set_image(self, ctx, url: str):
        config = load_config()
        config["welcome"]["image_url"] = url
        save_config(config)
        await ctx.send(f"✅ Welcome image updated!")

    @setwelcome.command(name="role", description="Set auto-role")
    async def set_autorole(self, ctx, role: discord.Role):
        config = load_config()
        config["auto_role_id"] = role.id
        save_config(config)
        await ctx.send(f"✅ Auto-Role set to **{role.name}**")

    @commands.hybrid_command(name="testwelcome")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        await self.on_member_join(ctx.author)
        await ctx.send("✅ Test message sent!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
              
