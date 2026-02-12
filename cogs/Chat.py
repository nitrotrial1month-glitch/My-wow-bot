import discord
from discord.ext import commands
import aiohttp
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

    async def get_direct_response(self, text):
        if not GOOGLE_API_KEY:
            return "⚠️ API Key নেই! Railway তে চেক করুন।"

        # সরাসরি লিংক (Gemini 1.5 Flash)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": f"{self.system_prompt}\nUser: {text}\nWow:"}]
            }]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    # যদি সব ঠিক থাকে (200 OK)
                    if response.status == 200:
                        result = await response.json()
                        return result['candidates'][0]['content']['parts'][0]['text']
                    
                    # যদি কোটা শেষ হয় (429)
                    elif response.status == 429:
                        return "❌ কোটা শেষ! নতুন API Key দরকার।"
                    
                    # অন্য কোনো এরর
                    else:
                        error_text = await response.text()
                        print(f"Server Error: {error_text}") # কনসোলে দেখাবে
                        return f"⚠️ সার্ভার এরর: {response.status}"
                        
        except Exception as e:
            return f"❌ কোড এরর: {e}"

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
            embed = discord.Embed(description="Yes boss? I am ready! 🚀", color=discord.Color.green())
            await message.channel.send(embed=embed)
            return

        # ৪. চ্যাট লজিক (শুধু পিং বা রিপ্লাই হলে)
        if (is_mentioned and user_message) or is_reply:
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                if not user_message: user_message = message.content
                
                # রেসপন্স কল
                bot_reply = await self.get_direct_response(user_message)

                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
