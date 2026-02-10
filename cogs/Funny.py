import discord
from discord.ext import commands
import random

class Roleplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # --- GIF Links for Each Action ---
        self.kiss_gifs = [
            "https://media.giphy.com/media/bm2O3nXTcKJeU/giphy.gif",
            "https://media.giphy.com/media/bm2O3nXTcKJeU/giphy.gif",
            "https://media.giphy.com/media/bm2O3nXTcKJeU/giphy.gif",
            "https://media.giphy.com/media/bm2O3nXTcKJeU/giphy.gif",
            "https://media.giphy.com/media/bm2O3nXTcKJeU/giphy.gif",
            "https://media.giphy.com/media/bm2O3nXTcKJeU/giphy.gif"
        ]
        self.kill_gifs = [
            "https://media.giphy.com/media/3o7qDDfL1h8n39hCco/giphy.gif",
            "https.giphy.com/gifs/kill-anime-stab-QFCY9mK9v8g8U",
            "https://media.giphy.com/media/l41JRsrVb5qj4K1ws/giphy.gif",
            "https://media.giphy.com/media/eWFEhB9qg9vXoR1K2E/giphy.gif",
            "https://media.giphy.com/media/3ohhwh90nF3zKz9zji/giphy.gif"
        ]
        self.hug_gifs = [
            "https://media.giphy.com/media/LIQfC438yqfT8zK32y/giphy.gif",
            "https://media.giphy.com/media/u9gbT692s6XfO/giphy.gif",
            "https://media.giphy.com/media/xJlJglV2uQnVm/giphy.gif",
            "https://media.giphy.com/media/hnNy7y3NqYhXW/giphy.gif",
            "https://media.giphy.com/media/M3Q6R9fSg072tT200T/giphy.gif",
            "https.giphy.com/gifs/anime-couple-love-hug-cKsD0GjG1P9lC",
            "https://giphy.com/gifs/cute-anime-hug-LzG8d2LgI0Nn82i0Fm"
        ]
        self.slap_gifs = [
            "https://media.giphy.com/media/gYZz8PqY3L72g/giphy.gif",
            "https://media.giphy.com/media/ZkmiqhZs2iYOk/giphy.gif",
            "https://media.giphy.com/media/mGk6t4X0U2Nry/giphy.gif",
            "https://media.giphy.com/media/QhVz8QGz6jJgw/giphy.gif",
            "https://giphy.com/gifs/anime-girl-slap-yYp9yQy20N0pY1uT7w"
        ]
        self.bite_gifs = [
            "https://media.giphy.com/media/Q2jF6c07mK1UfK0Qp8/giphy.gif",
            "https://media.giphy.com/media/pUeXgW4xO7wA/giphy.gif",
            "https://media.giphy.com/media/3o7qDJB2qQJbLzX7xS/giphy.gif",
            "https://media.giphy.com/media/vJcM4z80f7fJ6/giphy.gif",
            "https://media.giphy.com/media/4g6j2nO48L6r8fN9yJ/giphy.gif"
        ]
        # NSFW 'Fuck' command will not have explicit gifs for safety, will use the emoji instead.
        # However, if you have a private, strict NSFW server and want to add specific gifs, you can.
        # self.fuck_gifs = ["your_nsfw_gif_link_here"]

    async def roleplay_embed(self, ctx, target, action_text, emoji, gif_list=None):
        if target == ctx.author:
            return await ctx.send(f"❌ You can't {ctx.invoked_with} yourself! That's a bit lonely, isn't it?", ephemeral=True)
        
        embed = discord.Embed(
            description=f"{emoji} | **{ctx.author.display_name}** {action_text} **{target.display_name}**!",
            color=0xff69b4 # Pinkish fun color
        )
        if gif_list:
            embed.set_image(url=random.choice(gif_list)) # রেন্ডম জিআইএফ সেট করা
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kiss", description="Kiss someone special!")
    async def kiss(self, ctx, member: discord.Member):
        await self.roleplay_embed(ctx, member, "gave a sweet kiss to", "💋", self.kiss_gifs)

    @commands.hybrid_command(name="kill", description="Kill your enemy!")
    async def kill(self, ctx, member: discord.Member):
        await self.roleplay_embed(ctx, member, "just ended", "⚔️", self.kill_gifs)

    @commands.hybrid_command(name="hug", description="Give someone a warm hug!")
    async def hug(self, ctx, member: discord.Member):
        await self.roleplay_embed(ctx, member, "gave a big warm hug to", "🫂", self.hug_gifs)

    @commands.hybrid_command(name="slap", description="Slap someone hard!")
    async def slap(self, ctx, member: discord.Member):
        await self.roleplay_embed(ctx, member, "slapped", "🖐️", self.slap_gifs)

    @commands.hybrid_command(name="bite", description="Bite someone! Ouch!")
    async def bite(self, ctx, member: discord.Member):
        await self.roleplay_embed(ctx, member, "bit", "🦷", self.bite_gifs)

    @commands.hybrid_command(name="fuck", description="Well... you know what this is.")
    async def fuck(self, ctx, member: discord.Member):
        if not ctx.channel.is_nsfw():
            return await ctx.send("🔞 This command can only be used in **NSFW** channels!", ephemeral=True)
        # NSFW Gifs are not included by default for safety.
        # If you want to add them, replace None with self.fuck_gifs (after defining self.fuck_gifs)
        await self.roleplay_embed(ctx, member, "is having some 'private time' with", "🔞", None)

async def setup(bot):
    await bot.add_cog(Roleplay(bot))
                  
