import discord
from discord.ext import commands
import google.generativeai as genai
import os
import random
import asyncio
import warnings

# --- 🚫 লাল ওয়ার্নিং লুকানোর কোড ---
warnings.filterwarnings("ignore") 
# ---------------------------------

# আপনার API Key
GOOGLE_API_KEY = "AIzaSyAqjoitOuE-4XyLBLWzK_6XqBrgmCLVE8k"

# কনফিগারেশন
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"❌ API Error: {e}")

# মডেল সেটআপ
model = genai.GenerativeModel('gemini-1.5-flash')

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋"]
        self.system_prompt = (
            "You are a helpful and friendly Discord bot named 'Wow'. "
            "Reply in Bengali or English. Keep answers short and funny."
        )

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
                description="Powered by **Gemini AI**! 🚀",
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
                try:
                    if not user_message: user_message = message.content
                    full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                    # API কল (Async)
                    response = await model.generate_content_async(full_prompt)
                    
                    bot_reply = response.text
                    
                    # মেসেজ বেশি বড় হলে ছোট করা
                    if len(bot_reply) > 2000:
                        bot_reply = bot_reply[:1990] + "..."
                        
                    await message.reply(bot_reply, mention_author=False)

                except Exception as e:
                    print(f"❌ Error: {e}")
                    await message.reply("😵‍💫 আমার ব্রেইন কানেক্ট হচ্ছে না! একটু পরে চেষ্টা করো।", mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
    
