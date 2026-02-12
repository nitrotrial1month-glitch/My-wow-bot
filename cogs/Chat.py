import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import random
import asyncio

# Retrieve API Key from Railway Variables
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
        
        # --- System Prompt for All Language Support ---
        self.system_prompt = (
            "You are a helpful, witty, and friendly Discord bot named 'Wow'. "
            "INSTRUCTION: Detect the language of the user's message and reply in the EXACT SAME language. "
            "Example: If user speaks Bengali, reply in Bengali. If English, reply in English. "
            "Keep your answers short, engaging, and fun (max 2-3 sentences)."
        )

    # --- Smart Response Function (Tries multiple models) ---
    async def get_ai_response(self, full_prompt):
        if not client:
            return "⚠️ API Key is missing in Railway Variables!"

        # List of models to try (Priority: 2.0 Flash -> 1.5 Flash -> 1.5 Pro)
        models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

        for model_name in models_to_try:
            try:
                # Attempt to generate content
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.8, # Creative but stable
                        max_output_tokens=200 
                    )
                )
                return response.text # Return if successful
            except Exception as e:
                print(f"⚠️ Model '{model_name}' failed: {e}")
                continue # Try the next model
        
        return "❌ All AI models are currently busy. Please try again later."

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return

        # 1. Clean the user message (Remove bot mentions)
        user_message = message.content.replace(f'<@!{self.bot.user.id}>', '').replace(f'<@{self.bot.user.id}>', '').strip()

        # 2. Check Triggers
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user)
        is_named = "wow" in message.content.lower().split()

        # 3. Logic: Just Ping (No Message) -> Show Info Embed
        if is_mentioned and not user_message:
            embed = discord.Embed(
                title="🤖 Hello! I am Wow",
                description="I am an advanced AI bot powered by **Google Gemini 2.0**! 🚀",
                color=discord.Color.from_rgb(0, 162, 255)
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            embed.add_field(name="🌍 Multi-Language", value="I speak **ALL Languages**! Just talk to me.", inline=False)
            embed.add_field(name="💬 How to use?", value="Simply ping me or reply to my messages.\nExample: `@Wow How are you?`", inline=False)
            embed.set_footer(text="Developed for You ❤️")
            
            await message.channel.send(embed=embed)
            return

        # 4. Logic: Chatting (Ping + Text OR Reply OR Name Call)
        if (is_mentioned and user_message) or is_reply or is_named:
            
            # Add a random reaction
            try: await message.add_reaction(random.choice(self.reactions))
            except: pass

            async with message.channel.typing():
                # Handle empty message in replies
                if not user_message: user_message = message.content
                
                # Create the prompt
                full_prompt = f"{self.system_prompt}\nUser: {user_message}\nWow:"

                # Get response using the smart function
                bot_reply = await self.get_ai_response(full_prompt)

                # Split message if too long (Discord limit 2000)
                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await message.reply(bot_reply, mention_author=False)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
