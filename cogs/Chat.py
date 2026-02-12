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
        
        # --- ১. অল ল্যাঙ্গুয়েজ সাপোর্ট প্রম্পট ---
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "IMPORTANT: Always detect the language of the user's message and reply in the EXACT SAME language. "
            "If they speak Bengali, reply in Bengali. If Hindi, reply in Hindi. If English, reply in English. "
            "Keep answers short, funny, and engaging."
        )

    # --- ২. মডেল ফিক্সার ফাংশন (স্মার্ট সলিউশন) ---
    async def get_response(self, prompt):
        # প্রথমে লেটেস্ট মডেল দিয়ে ট্রাই করবে
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async(prompt)
            return response.text
        except:
            # যদি 404 আসে, তবে পুরনো স্টেবল মডেল দিয়ে ট্রাই করবে
            try:
                model = genai.GenerativeModel('gemini-pro')
                response = await model.generate_content_async(prompt)
                return response.text
            except Exception as e:
                return f"Error: {e}"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ক্লিন মেসেজ
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ট্রিগার কন্ডিশন
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # শুধু পিং করলে ইনফো
        if self.bot.user in message.mentions and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I speak **ALL Languages**! Just talk to me. 🌍",
                color=discord.Color.blue()
            )
            embed.add_field(name="💬 Chat", value="Ping me and say something!\nExample: `@Wow কেমন আছো?`", inline=False)
            await message.channel.send(embed=embed)
            return

        # চ্যাটিং লজিক
        if (is_mentioned and user_message) or is_reply or is_named:
            
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                if not user_message: user_message = message.content
                
                # প্রম্পট রেডি করা
                full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                # স্মার্ট ফাংশন দিয়ে রেসপন্স নেওয়া
                bot_reply = await self.get_response(full_prompt)

                # মেসেজ লিমিট চেক
                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
