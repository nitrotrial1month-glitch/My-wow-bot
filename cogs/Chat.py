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
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in Bengali or English. Keep answers short and funny."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ১. ক্লিন মেসেজ তৈরি
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ২. ট্রিগার কন্ডিশন
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # ৩. শুধু পিং করলে ইনফো
        if self.bot.user in message.mentions and not user_message:
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
            
            # রেন্ডম রিঅ্যাকশন
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                try:
                    if not user_message: user_message = message.content

                    full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                    # API কল (মডেলের নাম পরিবর্তন করা হয়েছে)
                    response = await client.aio.models.generate_content(
                        model='gemini-1.5-flash-002', # আপডেট করা মডেল নেম
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.9,
                            max_output_tokens=150,
                        )
                    )
                    
                    bot_reply = response.text
                    await message.reply(bot_reply, mention_author=False)

                except Exception as e:
                    print(f"❌ Error in AI Reply: {e}")
                    # যদি ফ্ল্যাশ মডেল কাজ না করে, তবে প্রো মডেলে ট্রাই করবে (ব্যাকআপ)
                    try:
                        response = await client.aio.models.generate_content(
                            model='gemini-1.5-pro',
                            contents=full_prompt
                        )
                        await message.reply(response.text, mention_author=False)
                    except:
                        await message.channel.send(f"⚠️ আমার সার্ভারে একটু সমস্যা হচ্ছে! (Error: 404/Model Not Found)")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
                    
