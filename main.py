import discord
from discord.ext import commands
import json
import os
import asyncio
from utils import load_config

# ================= 1. প্রিফিক্স সেটআপ (Wow) =================
def get_prefix(bot, message):
    """সার্ভার অনুযায়ী প্রিফিক্স লোড করে (Default: Wow)"""
    try:
        if os.path.exists('prefixes.json'):
            with open('prefixes.json', 'r') as f:
                prefixes = json.load(f)
            # যদি সার্ভারে কোনো প্রিফিক্স সেট না থাকে, তবে "Wow" ব্যবহার করবে
            return prefixes.get(str(message.guild.id), "Wow")
    except:
        pass
    return "Wow"  # ডিফল্ট প্রিফিক্স

# ================= 2. মেইন বট ক্লাস =================
class NovaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,   # ডিফল্ট হেল্প বন্ধ
            case_insensitive=True, # Wow/wow দুটোই কাজ করবে
            strip_after_prefix=True # 'Wow help' এবং 'Wowhelp' দুটোই কাজ করবে
        )

    async def setup_hook(self):
        print("🔄 Initializing Wow System...")
        
        # 'cogs' ফোল্ডার থেকে ফাইল লোড
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f"  ✅ Loaded: {filename}")
                    except Exception as e:
                        print(f"  ❌ Failed: {filename} -> {e}")
        else:
            print("  ⚠️ 'cogs' folder missing!")

        # স্ল্যাশ কমান্ড সিঙ্ক
        print("🔄 Syncing Commands...")
        try:
            synced = await self.tree.sync()
            print(f"  🛰️ Synced {len(synced)} Slash Commands!")
        except Exception as e:
            print(f"  ⚠️ Sync Error: {e}")

# ================= 3. রানার এবং ইভেন্টস =================

bot = NovaBot()

@bot.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"""
    ╔══════════════════════════════════════════════╗
    ║            👑 WOW SYSTEM ONLINE 👑           ║
    ╠══════════════════════════════════════════════╣
    ║ 🤖 Bot Name   : {bot.user.name}             
    ║ 🆔 Bot ID     : {bot.user.id}               
    ║ 🗣️ Prefix     : Wow                         
    ║ 💎 System     : Active                      
    ╚══════════════════════════════════════════════╝
    """)
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name="Wowhelp | /help"
        ),
        status=discord.Status.online
    )

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

# ================= 4. টোকেন রান =================

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        try:
            bot.run(token)
        except Exception as e:
            print(f"\n❌ Login Error: {e}")
    else:
        print("\n❌ Error: DISCORD_TOKEN not found in Environment Variables!")
        
