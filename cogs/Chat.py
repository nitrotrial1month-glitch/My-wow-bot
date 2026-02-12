import discord
from discord.ext import commands
import google.generativeai as genai
import os
import random
import asyncio

# আপনার API Key
GOOGLE_API_KEY = "AIzaSyAqjoitOuE-4XyLBLWzK_6XqBrgmCLVE8k"

# কনফিগারেশন
genai.configure(api_key=GOOGLE_API_KEY)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in the SAME language as the user (Bengali/English/Hindi). "
            "Keep answers short, funny, and engaging."
        )
        # সব ধরনের মডেলের লিস্ট (বট একটার পর একটা ট্রাই করবে)
        self.backup_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
            "gemini-pro",
            "models/gemini-1.5-flash",
            "models/gemini-1.0-pro"
        ]

    async def get_smart_response(self, full_prompt):
        # লুপ চালিয়ে চেক করবে কোন মডেলটি কাজ করছে
        for model_name in self.backup_models:
            try:
                # মডেল লোড করা
                model = genai.GenerativeModel(model_name)
                # রেসপন্স নেওয়া
                response = await model.generate_content_async(full_prompt)
                return response.text # কাজ হলে সাথে সাথে রিটার্ন করবে
            except Exception as e:
                # কাজ না করলে পরের মডেল ট্রাই করবে
                print(f"⚠️ {model_name} failed, trying next...")
                continue
        
        return "❌ Error: আমার সার্ভার আপডেট হচ্ছে, কিছুক্ষণ পর চেষ্টা করো!"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ১. ক্লিন মেসেজ
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ২. ট্রিগার কন্ডিশন
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # ৩. শুধু পিং করলে ইনফো
        if self.bot.user in message.mentions and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I speak **ALL Languages**! Just talk to me. 🌍",
                color=discord.Color.blue()
            )
            embed.add_field(name="💬 Chat", value="Ping me and say something!", inline=False)
            await message.channel.send(embed=embed)
            return

        # ৪. চ্যাটিং লজিক
        if (is_mentioned and user_message) or is_reply or is_named:
            
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                if not user_message: user_message = message.content
                
                full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                # স্মার্ট ফাংশন কল
                bot_reply = await self.get_smart_response(full_prompt)

                # মেসেজ লিমিট চেক
                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
