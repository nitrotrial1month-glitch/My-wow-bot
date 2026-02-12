import discord
from discord.ext import commands
import aiohttp # এটি ডিসকর্ডের সাথেই থাকে
import os
import random

# Railway থেকে API Key নেওয়া
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]
        
        # সিস্টেম প্রম্পট
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in the SAME language as the user (Bengali/English/Hindi). "
            "Keep answers short, funny, and engaging."
        )

    # --- সরাসরি গুগলে রিকোয়েস্ট পাঠানোর ফাংশন (No Library) ---
    async def get_direct_response(self, text):
        if not GOOGLE_API_KEY:
            return "⚠️ API Key পাওয়া যায়নি! Railway Variables চেক করুন।"

        # সরাসরি লিংক ব্যবহার করা হচ্ছে (লাইব্রেরি ছাড়া)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": f"{self.system_prompt}\nUser: {text}\nWow:"}]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    try:
                        return result['candidates'][0]['content']['parts'][0]['text']
                    except:
                        return "🤔 উত্তর বুঝতে পারছি না!"
                elif response.status == 429:
                    return "❌ আমার কোটা শেষ! (Quota Exceeded). দয়া করে নতুন একটি API Key দিন।"
                else:
                    return f"❌ Server Error: {response.status}"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ক্লিন মেসেজ
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ১. ট্রিগার চেক
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        
        # ❌ নাম ধরে ডাকলে আর কাজ করবে না (Removed 'is_named')

        # ২. শুধু পিং করলে ইনফো দেখাবে
        if is_mentioned and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I am ready to chat! 🚀",
                color=discord.Color.green()
            )
            embed.add_field(name="💬 Usage", value="**Ping me** (`@Wow hello`) or **Reply** to my message to chat!", inline=False)
            await message.channel.send(embed=embed)
            return

        # ৩. চ্যাট লজিক (শুধু মেনশন অথবা রিপ্লাই হলে কাজ করবে)
        if (is_mentioned and user_message) or is_reply:
            
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                if not user_message: user_message = message.content
                
                # ডাইরেক্ট ফাংশন কল
                bot_reply = await self.get_direct_response(user_message)

                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
    
