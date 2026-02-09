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

import discord
from discord.ext import commands
from typing import Optional, Union

# ... আগের কোডগুলো এখানে থাকবে ...

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, roles: commands.Greedy[discord.Role]):
    """
    Locks the channel for mentioned roles or @everyone if no role is mentioned.
    Usage: !lock @Role1 @Role2  OR  !lock
    """
    # যদি কোনো রোল মেনশন না করা হয়, তবে @everyone রোলটি নিবে
    target_roles = roles if roles else [ctx.guild.default_role]
    
    locked_roles = []
    
    for role in target_roles:
        # ওই রোলের জন্য মেসেজ পাঠানোর পারমিশন বন্ধ করে দিচ্ছে
        await ctx.channel.set_permissions(role, send_messages=False)
        locked_roles.append(role.name)
    
    role_names = ", ".join(locked_roles)
    await ctx.send(f"🔒 Channel has been locked for: **{role_names}**")

@lock.error
async def lock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Your don't have `Manage Channels` permission to use this command.")
        

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: No DISCORD_TOKEN found in environment variables.")
      
