import discord
from discord.ext import commands
import aiohttp
import os
import random
import asyncio

# Railway Variable থেকে API Key নেওয়া
GOOGLE_API_KEY = AIzaSyA-oDTzSipRGiiTetFuJSRgVsAVt92v_rQ

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]
        
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in the SAME language as the user (Bengali/English/Hindi). "
            "Keep answers short (max 2 sentences), funny, and engaging."
        )

        # --- মডেলের লিস্ট (অগ্রাধিকার অনুযায়ী) ---
        self.models = [
            "gemini-3.0-flash"
            "gemini-2.0-flash",       # লেটেস্ট এবং সুপার ফাস্ট (First Priority)
            "gemini-1.5-flash",       # স্টেবল এবং নির্ভরযোগ্য
            "gemini-1.5-flash-latest",
            "gemini-pro"              # পুরনো কিন্তু ব্যাকআপ হিসেবে ভালো
        ]

    async def get_direct_response(self, text):
        if not GOOGLE_API_KEY:
            return "⚠️ API Key নেই! Railway তে চেক করুন।"

        async with aiohttp.ClientSession() as session:
            # একটার পর একটা মডেল ট্রাই করবে
            for model in self.models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=AIzaSyA-oDTzSipRGiiTetFuJSRgVsAVt92v_rQ"
                
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{
                        "parts": [{"text": f"{self.system_prompt}\nUser: {text}\nWow:"}]
                    }]
                }

                try:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result['candidates'][0]['content']['parts'][0]['text']
                        
                        elif response.status == 404:
                            print(f"⚠️ {model} পাওয়া যায়নি, পরেরটি দেখছি...")
                            continue # পরের মডেলে যাবে
                        
                        elif response.status == 429:
                            print(f"⚠️ {model} এর কোটা শেষ, পরেরটি দেখছি...")
                            continue

                except Exception as e:
                    print(f"Error checking {model}: {e}")
                    continue
            
            return "❌ দুঃখিত! আমার ব্রেইন এখন কাজ করছে না (API Key বা কোটা সমস্যা)।"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ১. ক্লিন মেসেজ
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ২. ট্রিগার চেক
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)

        # ৩. শুধু পিং করলে ইনফো
        if is_mentioned and not user_message:
            embed = discord.Embed(
                description="⚡ I am running on **Gemini Flash 2.0**! Super Fast! 🚀",
                color=discord.Color.gold()
            )
            await message.channel.send(embed=embed)
            return

        # ৪. চ্যাট লজিক
        if (is_mentioned and user_message) or is_reply:
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                if not user_message: user_message = message.content
                
                bot_reply = await self.get_direct_response(user_message)

                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
