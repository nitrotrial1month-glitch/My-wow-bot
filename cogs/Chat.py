import discord
from discord.ext import commands
import google.generativeai as genai
import random
import asyncio

# 🔴 আপনার API Key
GOOGLE_API_KEY = "AIzaSyDNm6_j5DcN8l0UtVeQGzSDg7v-PUtVzGo"

# জেমিনাই কনফিগারেশন
genai.configure(api_key=GOOGLE_API_KEY)

# ফাস্ট রেসপন্সের জন্য কনফিগারেশন
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 150, # উত্তর ছোট হবে তাই ফাস্ট আসবে
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config=generation_config,
    safety_settings=safety_settings
)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # রেনডম রিঅ্যাকশন লিস্ট
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
            
            # ১. রেনডম রিঅ্যাকশন দেওয়া
            try:
                emoji = random.choice(self.reactions)
                await message.add_reaction(emoji)
            except:
                pass # পারমিশন না থাকলে ইগনোর করবে

            # ২. টাইপিং এবং রিপ্লাই
            async with message.channel.typing():
                try:
                    user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').strip()
                    if not user_message: user_message = "Hello!"

                    prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                    # এপিআই কল (Timeout যোগ করা হয়েছে যাতে হ্যাং না করে)
                    response = await asyncio.wait_for(
                        model.generate_content_async(prompt), 
                        timeout=10.0 # ১০ সেকেন্ডের বেশি সময় নিলে এরর দিবে
                    )
                    
                    bot_reply = response.text
                    await message.reply(bot_reply, mention_author=False)

                except asyncio.TimeoutError:
                    await message.reply("Time out! আমার নেটে সমস্যা হচ্ছে, আবার চেষ্টা করো। 🐢")
                    print("Error: Gemini API Timeout")

                except Exception as e:
                    # এখানে আসল এরর দেখা যাবে
                    await message.reply(f"Error: আমি রিপ্লাই দিতে পারছি না! (Check Console)")
                    print(f"❌ Gemini API Error: {e}") 
                    # কনসোলে গিয়ে দেখুন কি লেখা আসছে (যেমন: Invalid API Key)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
    
