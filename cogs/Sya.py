import discord
from discord.ext import commands
from discord import app_commands
from utils import load_config, get_theme_color

class TalkSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_premium(self, guild_id):
        """Checks for Server Premium status"""
        return get_theme_color(guild_id) == discord.Color.gold()

    # --- 🗣️ Say Command (Hybrid) ---
    @commands.hybrid_command(name="say", description="🗣️ [PREMIUM] Make the bot speak")
    @app_commands.describe(message="What should I say?")
    async def say(self, ctx, message: str):
        if not self.is_premium(ctx.guild.id):
            return await ctx.send("💎 This command is restricted to **Premium Servers**.", ephemeral=True)

        # Delete user trigger message for prefix commands
        if ctx.interaction is None:
            try: await ctx.message.delete()
            except: pass

        await ctx.send(message)

    # --- 🖼️ Embed Command (Hybrid) ---
    @commands.hybrid_command(name="embed", description="🖼️ [PREMIUM] Send a stylish embed message")
    @app_commands.describe(title="Title of the embed", content="Main message")
    async def embed(self, ctx, title: str, content: str):
        if not self.is_premium(ctx.guild.id):
            return await ctx.send("💎 Unlock custom embeds with `/buy_premium`.", ephemeral=True)

        color = get_theme_color(ctx.guild.id)
        
        # Design (Nova Style)
        description = (
            f"### {title}\n"
            f"────────────────────\n"
            f"{content}\n"
            f"────────────────────"
        )
        
        embed = discord.Embed(description=description, color=color)
        embed.set_footer(text=f"Message by {ctx.author.display_name}")

        if ctx.interaction is None:
            try: await ctx.message.delete()
            except: pass

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TalkSystem(bot))
