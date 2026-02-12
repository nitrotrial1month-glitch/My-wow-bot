import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import random
import asyncio

# Retrieve API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Client
client = None
if GOOGLE_API_KEY:
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"❌ Client Setup Error: {e}")

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reactions = ["🔥", "👀", "🤖", "⚡", "😂", "🤔", "👋", "✨"]
        
        self.system_prompt = (
            "You are a helpful, witty, and friendly Discord bot named 'Wow'. "
            "INSTRUCTION: Detect the language of the user's message and reply in the EXACT SAME language. "
            "Keep your answers short, engaging, and fun (max 2-3 sentences)."
        )

        # --- 🔄 Model Rotation List (Backup Strategy) ---
        # If the first one fails (Limit Reached), it will use the next one.
        self.models_list = [
            "gemini-2.0-flash",       # Latest & Fastest (First Priority)
            "gemini-1.5-flash",       # Stable & High Limit
            "gemini-1.5-flash-8b",    # Very Fast & Cheap
            "gemini-1.5-pro",         # Smarter but slower
            "gemini-1.0-pro"          # Oldest but reliable backup
        ]

    # --- 🧠 Smart Response Function (Auto-Switching) ---
    async def get_ai_response(self, full_prompt):
        if not client:
            return "⚠️ API Key is missing in Railway Variables!"

        # Loop through all available models
        for model_name in self.models_list:
            try:
                # print(f"🔄 Trying model: {model_name}...") # Debugging Line
                
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=200 
                    )
                )
                return response.text # Success! Return the answer.
            
            except Exception as e:
                # If Error 429 (Limit Reached) or 404 (Not Found) occurs, ignore and try next.
                print(f"⚠️ Model '{model_name}' failed or limit reached. Switching...")
                continue # Jump to the next model in the list
        
        return "❌ My brain is tired! (Rate Limit Exceeded). Please wait 1 minute."

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # 1. Clean Message
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # 2. Check Triggers
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # 3. Logic: Just Ping
        if is_mentioned and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I am an advanced AI bot powered by **Google Gemini**! 🚀",
                color=discord.Color.blue()
            )
            embed.add_field(name="💬 Chat", value="Ping me and say something!", inline=False)
            await message.channel.send(embed=embed)
            return

        # 4. Logic: Chatting
        if (is_mentioned and user_message) or is_reply or is_named:
            
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                if not user_message: user_message = message.content
                
                full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                # Call the smart function
                bot_reply = await self.get_ai_response(full_prompt)

                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
    
