import discord
from discord.ext import commands
import aiohttp # ডিসকর্ডের সাথেই থাকে, আলাদা ইনস্টল লাগবে না
import os
import json
import random

# Railway Variable থেকে API Key নেওয়া
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

    # --- সরাসরি ইন্টারনেটের মাধ্যমে গুগলে কানেক্ট করা ---
    async def get_direct_response(self, text):
        if not GOOGLE_API_KEY:
            return "⚠️ API Key পাওয়া যায়নি! Railway Variables চেক করুন।"

        # আমরা সরাসরি gemini-1.5-flash ব্যবহার করব (সবচেয়ে ফাস্ট ও স্টেবল)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": f"{self.system_prompt}\nUser: {text}\nWow:"}]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                # যদি সফল হয় (Status 200)
                if response.status == 200:
                    result = await response.json()
                    try:
                        return result['candidates'][0]['content']['parts'][0]['text']
                    except:
                        return "🤔 উত্তর বুঝতে পারছি না!"
                
                # যদি কোটা শেষ হয়ে যায় (Status 429)
                elif response.status == 429:
                    return "❌ আমার দৈনিক লিমিট শেষ! (Quota Exceeded). দয়া করে নতুন একটি API Key ব্যবহার করুন।"
                
                # অন্য কোনো এরর হলে
                else:
                    error_text = await response.text()
                    print(f"❌ API Error: {response.status} - {error_text}")
                    return f"⚠️ সার্ভার এরর: {response.status} (Check Console)"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ক্লিন মেসেজ
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ট্রিগার চেক
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # ইনফো মেসেজ
        if self.bot.user in message.mentions and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="Powered by **Direct API (No Library)**! 🚀",
                color=discord.Color.green()
            )
            embed.add_field(name="💬 Chat", value="Ping me and say something!", inline=False)
            await message.channel.send(embed=embed)
            return

        # চ্যাট লজিক
        if (is_mentioned and user_message) or is_reply or is_named:
            
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
            
