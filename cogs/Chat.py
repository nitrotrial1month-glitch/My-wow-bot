import discord
from discord.ext import commands
import google.generativeai as genai
import os
import random
import asyncio

# --- Railway থেকে API Key নেওয়া ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

# যদি কি না পায়, তবে এরর দিবে
if not GOOGLE_API_KEY:
    print("❌ Error: GOOGLE_API_KEY not found in Environment Variables!")
else:
    # কনফিগারেশন
    genai.configure(api_key=GOOGLE_API_KEY)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]
        
        # সিস্টেম প্রম্পট (অল ল্যাঙ্গুয়েজ সাপোর্ট)
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in the SAME language as the user (Bengali/English/Hindi). "
            "Keep answers short, funny, and engaging."
        )

        # ব্যাকআপ মডেল লিস্ট
        self.backup_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
            "gemini-pro"
        ]

    async def get_smart_response(self, full_prompt):
        # যদি API Key না থাকে
        if not GOOGLE_API_KEY:
            return "⚠️ API Key সেট করা হয়নি!"

        for model_name in self.backup_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = await model.generate_content_async(full_prompt)
                return response.text
            except Exception:
                continue # ফেইল হলে পরের মডেল ট্রাই করবে
        
        return "❌ Error: সার্ভার বিজি আছে, পরে চেষ্টা করো।"

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
                description="I speak **ALL Languages**! Just talk to me. 🌍",
                color=discord.Color.blue()
            )
            embed.add_field(name="💬 Chat", value="Ping me and say something!", inline=False)
            await message.channel.send(embed=embed)
            return

        # চ্যাট রিপ্লাই
        if (is_mentioned and user_message) or is_reply or is_named:
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                if not user_message: user_message = message.content
                full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                bot_reply = await self.get_smart_response(full_prompt)

                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
