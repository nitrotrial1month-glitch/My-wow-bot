import discord
from discord.ext import commands
import json
import os

# প্রিফিক্স লোডার (রাখবেন)
def get_prefix(bot, message):
    try:
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
        return prefixes.get(str(message.guild.id), "Wow")
    except:
        return "Wow"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(
            command_prefix=get_prefix, 
            intents=intents,
            strip_after_prefix=True
        )
        
    async def setup_hook(self):
        # কগ লোডিং লজিক (রাখবেন)
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f"✅ Loaded: {filename}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
