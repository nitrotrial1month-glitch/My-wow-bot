import discord
from discord.ext import commands
from google import genai # নতুন ইম্পোর্ট
from google.genai import types # কনফিগারেশনের জন্য
import random
import asyncio

# 🔴 আপনার API Key
GOOGLE_API_KEY = "AIzaSyDNm6_j5DcN8l0UtVeQGzSDg7v-PUtVzGo"

# নতুন ক্লায়েন্ট সেটআপ
client = genai.Client(api_key=GOOGLE_API_KEY)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "❤️", "👋", "💬", "✨"]
        self.system_prompt = (
            "You are a helpful and funny Discord bot named 'Wow'. "
            "Reply in Bengali or English based on user language. "
            "Keep answers very short (1-2 sentences) and fast."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ট্রিগার চেক
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        if is_mentioned or is_reply or is_named:
            
            # ১. রেনডম রিঅ্যাকশন
            try:
                emoji = random.choice(self.reactions)
                await message.add_reaction(emoji)
            except:
                pass 

            # ২. টাইপিং এবং রিপ্লাই
            async with message.channel.typing():
                try:
                    user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').strip()
                    if not user_message: user_message = "Hello!"

                    full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                    # --- নতুন জেমিনাই কোড (Async) ---
                    response = await client.aio.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.9,
                            top_p=1.0,
                            top_k=1,
                            max_output_tokens=150, # ফাস্ট রেসপন্সের জন্য
                        )
                    )
                    
                    bot_reply = response.text
                    await message.reply(bot_reply, mention_author=False)

                except Exception as e:
                    # এখন আর ওয়ার্নিং আসবে না, কিন্তু অন্য কোনো এরর হলে দেখাবে
                    print(f"❌ GenAI Error: {e}")
                    await message.add_reaction("😵‍💫")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
    
