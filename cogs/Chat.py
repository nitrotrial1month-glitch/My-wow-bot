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
            "Reply in Bengali or English based on the user's language. "
            "Keep answers short (max 2 sentences), funny, and engaging."
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

                    # --- MULTI-MODEL TRY LOGIC ---
                    # আমরা এক এক করে ৩টি মডেল ট্রাই করব। যেটা কাজ করবে সেটাই উত্তর দেবে।
                    models_to_try = [
                        "gemini-2.0-flash",       # লেটেস্ট এবং ফাস্ট
                        "gemini-1.5-flash",       # স্ট্যান্ডার্ড
                        "gemini-1.5-flash-002",   # অল্টারনেটিভ ভার্সন
                        "gemini-1.5-pro"          # পাওয়ারফুল ব্যাকআপ
                    ]

                    response_text = None

                    for model_name in models_to_try:
                        try:
                            print(f"🔄 Trying model: {model_name}...") # কনসোলে দেখাবে কোন মডেল ট্রাই করছে
                            response = await client.aio.models.generate_content(
                                model=model_name,
                                contents=full_prompt,
                                config=types.GenerateContentConfig(
                                    temperature=0.9,
                                    max_output_tokens=150,
                                )
                            )
                            response_text = response.text
                            print(f"✅ Success with: {model_name}")
                            break # সফল হলে লুপ ব্রেক করবে
                        except Exception as e:
                            print(f"⚠️ Failed {model_name}: {e}")
                            continue # ফেইল হলে পরের মডেল ট্রাই করবে

                    # যদি সব মডেল ফেইল করে
                    if response_text:
                        await message.reply(response_text, mention_author=False)
                    else:
                        await message.reply("😵‍💫 আমার ব্রেইন কানেক্ট হচ্ছে না! (All models failed)", mention_author=False)

                except Exception as e:
                    print(f"❌ Critical Error: {e}")
                    await message.channel.send(f"⚠️ Error: {e}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
