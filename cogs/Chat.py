import discord
from discord.ext import commands
from google import genai
from google.genai import types
import random
import asyncio

# 🔴 আপনার নতুন API Key
GOOGLE_API_KEY = "AIzaSyAqjoitOuE-4XyLBLWzK_6XqBrgmCLVE8k"

# Google GenAI ক্লায়েন্ট সেটআপ
client = genai.Client(api_key=GOOGLE_API_KEY)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "❤️", "👋", "💬", "✨"]
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in Bengali or English based on the user's language. "
            "Keep answers short, funny, and engaging."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ১. মেসেজ ক্লিন করা (বটের মেনশন রিমুভ করে আসল টেক্সট বের করা)
        # <@12345> এবং <@!12345> দুটি ফরম্যাটই রিমুভ করা হচ্ছে
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ২. লজিক: শুধু পিং করলে ইনফো দেখাবে
        if self.bot.user in message.mentions and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I am an advanced AI bot powered by **Gemini**! 🚀",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            embed.add_field(name="💬 Chat with me", value="Just ping me and say something!\nExample: `@Wow How are you?`", inline=False)
            embed.add_field(name="📜 Help Command", value="Type `/help` or `!help` to see my commands.", inline=False)
            embed.set_footer(text="Developed by You ❤️")
            
            return await message.channel.send(embed=embed)

        # ৩. লজিক: চ্যাটিং (পিং + মেসেজ অথবা রিপ্লাই)
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        if (is_mentioned and user_message) or is_reply or is_named:
            
            # রেনডম রিঅ্যাকশন
            try:
                await message.add_reaction(random.choice(self.reactions))
            except:
                pass 

            # টাইপিং ইন্ডিকেটর
            async with message.channel.typing():
                try:
                    # যদি রিপ্লাই বা নাম ধরে ডাকে, তখন user_message আপডেট করা হতে পারে
                    if not user_message: 
                        user_message = message.content # রিপ্লাইয়ের ক্ষেত্রে পুরো মেসেজ নেওয়া

                    full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                    # --- Google GenAI API Call ---
                    response = await client.aio.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.9,
                            top_p=1.0,
                            top_k=1,
                            max_output_tokens=150, # ফাস্ট রেসপন্স
                        )
                    )
                    
                    bot_reply = response.text
                    await message.reply(bot_reply, mention_author=False)

                except Exception as e:
                    print(f"❌ AI Error: {e}")
                    await message.add_reaction("😵‍💫")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
