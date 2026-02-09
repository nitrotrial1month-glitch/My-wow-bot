import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

class EmojiSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_emoji", description="Add an emoji to the server from a link or another emoji")
    @app_commands.describe(
        name="Name of the new emoji",
        emoji_source="The emoji itself or a direct image/gif link"
    )
    @app_commands.checks.has_permissions(manage_expressions=True)
    async def add_emoji(self, interaction: discord.Interaction, name: str, emoji_source: str):
        await interaction.response.defer() # কিছুটা সময় লাগতে পারে তাই ডিফার করা হলো

        # যদি সোর্সটি একটি ইমোজি হয় (Custom Emoji Format: <a:name:id> or <:name:id>)
        if emoji_source.startswith("<") and emoji_source.endswith(">"):
            emoji_id = emoji_source.split(":")[-1][:-1]
            is_animated = emoji_source.startswith("<a:")
            ext = "gif" if is_animated else "png"
            url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
        else:
            # যদি সোর্সটি সরাসরি একটি লিঙ্ক হয়
            url = emoji_source

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return await interaction.followup.send("❌ Could not download the image. Make sure the link is valid.")
                    
                    image_data = await response.read()
                    
                    # সার্ভারে ইমোজি আপলোড করা
                    new_emoji = await interaction.guild.create_custom_emoji(name=name, image=image_data)
                    await interaction.followup.send(f"✅ Successfully added the emoji: {new_emoji} as `:{name}:`")
            
            except discord.HTTPException as e:
                await interaction.followup.send(f"❌ Failed to add emoji. Error: {e}")
            except Exception as e:
                await interaction.followup.send(f"❌ An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(EmojiSystem(bot))
