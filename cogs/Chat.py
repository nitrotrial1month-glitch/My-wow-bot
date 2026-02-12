import discord
from discord.ext import commands
import google.generativeai as genai
import os
import random
import asyncio

# ENV থেকে API KEY নেবে (Railway Safe)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is not set!")

genai.configure(api_key=GOOGLE_API_KEY)

# ─── INTENTS ─────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]

        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in the SAME language as the user (Bengali/English/Hindi). "
            "Keep replies short, fun, and engaging."
        )

        self.backup_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
            "gemini-pro"
        ]

    def get_smart_response(self, full_prompt: str) -> str:
        for model_name in self.backup_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                print(f"⚠️ {model_name} failed: {e}")
                continue

        return "❌ Sorry! My brain is reloading. Try again later 😵‍💫"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Mention clean
        user_message = (
            message.content
            .replace(f'<@!{self.bot.user.id}>', '')
            .replace(f'<@{self.bot.user.id}>', '')
            .strip()
        )

        is_mentioned = self.bot.user in message.mentions
        is_reply = (
            message.reference
            and message.reference.resolved
            and message.reference.resolved.author == self.bot.user
        )
        is_named = "wow" in message.content.lower().split()

        # Only ping info
        if is_mentioned and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I can chat in **Bengali, English & Hindi** 🌍\nJust mention me!",
                color=discord.Color.blurple()
            )
            await message.channel.send(embed=embed)
            return

        if (is_mentioned and user_message) or is_reply or is_named:

            try:
                await message.add_reaction(random.choice(self.reactions))
            except:
                pass

            async with message.channel.typing():
                if not user_message:
                    user_message = message.content

                prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                loop = asyncio.get_event_loop()
                bot_reply = await loop.run_in_executor(
                    None, self.get_smart_response, prompt
                )

                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

        # 🔴 VERY IMPORTANT
        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(AIChat(bot))
