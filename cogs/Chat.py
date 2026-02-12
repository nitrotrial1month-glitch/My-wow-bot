import discord
from discord.ext import commands
import google.generativeai as genai
import os

# 🔴 আপনার দেওয়া API Key টি এখানে বসানো হয়েছে
GOOGLE_API_KEY = "AIzaSyDNm6_j5DcN8l0UtVeQGzSDg7v-PUtVzGo"

# জেমিনাই কনফিগারেশন
genai.configure(api_key=GOOGLE_API_KEY)

# সেফটি সেটিংস (যাতে আজেবাজে উত্তর না দেয়)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# মডেল লোড করা
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash', 
    safety_settings=safety_settings
)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # বটের পার্সোনালিটি
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "You speak in Bengali (Bangla) or English depending on the user's language. "
            "Keep your answers short, funny, and engaging. Do not write long paragraphs."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        # ১. বট নিজের মেসেজে রিপ্লাই দেবে না
        if message.author.bot:
            return

        # ২. ট্রিগার চেক করা (Trigger Checks)
        
        # ক) কেউ কি বটকে মেনশন করেছে? (@Wow)
        is_mentioned = self.bot.user in message.mentions
        
        # খ) কেউ কি বটের মেসেজে রিপ্লাই দিয়েছে? (Reply)
        is_reply = False
        if message.reference and message.reference.resolved:
            if message.reference.resolved.author == self.bot.user:
                is_reply = True

        # গ) কেউ কি বটের নাম "wow" ধরে ডেকেছে? (Case Insensitive)
        content_lower = message.content.lower().split()
        is_named = "wow" in content_lower

        # ৩. যদি উপরের কোনো একটি শর্ত সত্য হয়, তবেই বট উত্তর দিবে
        if is_mentioned or is_reply or is_named:
            
            # টাইপিং ইন্ডিকেটর দেখানো
            async with message.channel.typing():
                try:
                    # ইউজারের মেসেজ প্রসেস করা (মেনশন ট্যাগ সরিয়ে ফেলা)
                    user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').strip()
                    
                    # যদি মেসেজ খালি হয়
                    if not user_message:
                        user_message = "Hello! 👋"

                    # প্রম্পট তৈরি করা
                    prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                    # জেমিনাই এপিআই কল করা (Async)
                    response = await model.generate_content_async(prompt)
                    bot_reply = response.text

                    # মেসেজ বেশি বড় হলে ছোট করা
                    if len(bot_reply) > 2000:
                        bot_reply = bot_reply[:1990] + "..."

                    # রিপ্লাই পাঠানো
                    await message.reply(bot_reply, mention_author=False)

                except Exception as e:
                    print(f"Gemini API Error: {e}")
                    # এরর হলে কিছু বলবে না বা সিম্পল ইমোজি দিবে
                    await message.add_reaction("😵‍💫")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
  
