import discord
from discord.ext import commands
from google import genai
from google.genai import types
import random
import asyncio

# আপনার API Key
GOOGLE_API_KEY = "AIzaSyAqjoitOuE-4XyLBLWzK_6XqBrgmCLVE8k"

# ক্লায়েন্ট সেটআপ
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"❌ API Client Error: {e}")

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂"]
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in Bengali or English. Keep answers short and funny."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ডিবাগ প্রিন্ট: কনসোলে দেখাবে মেসেজ আসছে কিনা
        # print(f"📩 Message received: {message.content} from {message.author}")

        # ১. ক্লিন মেসেজ তৈরি
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ২. ট্রিগার কন্ডিশন
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # ৩. শুধু পিং করলে ইনফো
        if self.bot.user in message.mentions and not user_message:
            print("✅ Ping Detected! Sending Embed...")
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="Powered by **Gemini AI**! 🚀",
                color=discord.Color.blue()
            )
            embed.add_field(name="💬 Chat", value="Ping me and say something!", inline=False)
            await message.channel.send(embed=embed)
            return

        # ৪. চ্যাটিং লজিক
        if (is_mentioned and user_message) or is_reply or is_named:
            print(f"✅ AI Triggered! Prompt: {user_message}")
            
            async with message.channel.typing():
                try:
                    if not user_message: user_message = message.content

                    full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                    # API কল
                    response = await client.aio.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.9,
                            max_output_tokens=150,
                        )
                    )
                    
                    bot_reply = response.text
                    print("✅ Reply Generated!")
                    await message.reply(bot_reply, mention_author=False)

                except Exception as e:
                    print(f"❌ Error in AI Reply: {e}")
                    await message.channel.send(f"⚠️ Error: {e}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
    
