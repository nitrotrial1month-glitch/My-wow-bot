import discord
from discord.ext import commands
import google.generativeai as genai
import os
import random
import asyncio
import warnings

# ওয়ার্নিং হাইড করা
warnings.filterwarnings("ignore")

# Railway থেকে API Key নেওয়া
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]
        
        # সিস্টেম প্রম্পট (ল্যাঙ্গুয়েজ ডিটেকশন সহ)
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in the SAME language as the user (Bengali/English/Hindi). "
            "Keep answers short, funny, and engaging."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # ক্লিন মেসেজ
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # ট্রিগার চেক
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # ইনফো মেসেজ (শুধু পিং করলে)
        if self.bot.user in message.mentions and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I am powered by **Google Gemini**! 🚀",
                color=discord.Color.blue()
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
                
                full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                try:
                    # লেটেস্ট মডেল ব্যবহার করা হচ্ছে
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = await model.generate_content_async(full_prompt)
                    
                    bot_reply = response.text
                    if len(bot_reply) > 2000:
                        bot_reply = bot_reply[:1990] + "..."
                    
                    await message.reply(bot_reply, mention_author=False)

                except Exception as e:
                    print(f"❌ Gemini Error: {e}")
                    # যদি ফ্ল্যাশ কাজ না করে, তবে প্রো দিয়ে ট্রাই করবে (ব্যাকআপ)
                    try:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        response = await model.generate_content_async(full_prompt)
                        await message.reply(response.text, mention_author=False)
                    except:
                        await message.reply("😵‍💫 আমার সার্ভার একটু ব্যস্ত আছে, পরে চেষ্টা করো!", mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
