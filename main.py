import os
import discord
from discord.ext import commands

# Fetching the token from Environment Variables (Important for Security)
TOKEN = os.getenv('DISCORD_TOKEN')

# Setting up bot intents
intents = discord.Intents.default()
intents.message_content = True

# Setting the command prefix
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is online and ready!')

@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! Latency: {round(bot.latency * 1000)}ms')

@bot.command()
async def hello(ctx):
    await ctx.send('Hello! I am a Python bot hosted on Railway.')

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: No DISCORD_TOKEN found in environment variables.")
      
