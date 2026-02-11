import discord
from discord.ext import commands
from discord import app_commands
from utils import check_advanced_premium

class TalkSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Helper: Premium Verification ---
    def is_premium(self, user_id, guild_id):
        u_status = check_advanced_premium(user_id)
        s_status = check_advanced_premium(None, guild_id)
        return u_status["active"] or s_status["active"]

    # ==========================================
    # 1. SAY COMMAND (Long: say, Short: s)
    # ==========================================
    @commands.hybrid_command(
        name="say", 
        description="🗣️ [PREMIUM] Make the bot repeat your words", 
        aliases=["tlk", "talk"]
    )
    @app_commands.describe(message="The message to say", channel="Target channel (optional)")
    async def say(self, ctx, message: str, channel: discord.TextChannel = None):
        # প্রিমিয়াম চেক
        if not self.is_premium(ctx.author.id, ctx.guild.id):
            return await ctx.send("💎 This command is for **Premium Members** only.", ephemeral=True)

        target_channel = channel or ctx.channel
        
        # পারমিশন চেক
        if not target_channel.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send(f"❌ I don't have permission to speak in {target_channel.mention}", ephemeral=True)

        # প্রিফিক্স কমান্ড হলে ইউজারের মেসেজটি ডিলিট করে দিবে (বট ফিল আনার জন্য)
        if ctx.interaction is None:
            try: await ctx.message.delete()
            except: pass

        await target_channel.send(message)
        
        # স্ল্যাশ কমান্ড হলে সাকসেস মেসেজ দিবে
        if ctx.interaction:
            await ctx.send(f"✅ Sent to {target_channel.mention}", ephemeral=True)

    # ==========================================
    # 2. EMBED COMMAND (Long: embed, Short: eb)
    # ==========================================
    @commands.hybrid_command(
        name="embed", 
        description="🖼️ [PREMIUM] Send a stylish embed message", 
        aliases=["eb", "esay"]
    )
    @app_commands.describe(title="Embed Title", description="Embed Content", color="Hex code (e.g. #ff0000)")
    async def embed(self, ctx, title: str, description: str, color: str = "#00ff00"):
        if not self.is_premium(ctx.author.id, ctx.guild.id):
            return await ctx.send("💎 This is a **Premium Only** feature.", ephemeral=True)

        # কালার কনভার্ট
        try:
            hex_color = int(color.replace("#", ""), 16)
        except:
            hex_color = 0x2ecc71 # Default Green

        embed = discord.Embed(title=title, description=description, color=hex_color)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        if ctx.interaction is None:
            try: await ctx.message.delete()
            except: pass

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TalkSystem(bot))
                               
