import discord
from discord.ext import commands
import json
import os
import asyncio
from utils import load_config # utils.py থেকে কনফিগ লোড

# ================= 1. প্রিফিক্স সেটআপ =================
def get_prefix(bot, message):
    """সার্ভার অনুযায়ী কাস্টম প্রিফিক্স লোড"""
    try:
        with open('prefixes.json', 'r') as f:
            prefixes = json.load(f)
        return prefixes.get(str(message.guild.id), "!") # ডিফল্ট প্রিফিক্স "!"
    except:
        return "!"

# ================= 2. মেইন বট ক্লাস =================
class NovaBot(commands.Bot):
    def __init__(self):
        # ইনটেন্টস (সব পারমিশন অন করা)
        intents = discord.Intents.all()
        intents.message_content = True
        intents.members = True 
        intents.presences = True

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,  # ❌ ডিফল্ট হেল্প কমান্ড বন্ধ করা হয়েছে
            case_insensitive=True, # ছোট/বড় হাতের অক্ষর সমস্যা করবে না
            strip_after_prefix=True
        )

    async def setup_hook(self):
        """Cog এবং Extension লোড করা"""
        print("🔄 Loading Extensions...")
        
        # 'cogs' ফোল্ডারের সব ফাইল লোড করা
        # আপনার বানানো ফাইলগুলো (DailyCommand.py, Profile.py, etc.) একটি 'cogs' ফোল্ডারে রাখবেন
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f"  ✅ Loaded: {filename}")
                    except Exception as e:
                        print(f"  ❌ Failed to load {filename}: {e}")
        else:
            print("⚠️ 'cogs' folder not found! Please create one.")

        # স্ল্যাশ কমান্ড সিঙ্ক করা
        print("🔄 Syncing Slash Commands...")
        try:
            synced = await self.tree.sync()
            print(f"  🛰️ Synced {len(synced)} Slash Commands!")
        except Exception as e:
            print(f"  ⚠️ Sync Error: {e}")

# ================= 3. গ্লোবাল রানার =================

bot = NovaBot()

@bot.event
async def on_ready():
    # কনসোল ক্লিয়ার করে সুন্দর লগ দেখানো
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"""
    ╔═════════════════════════════════════════╗
    ║        🚀 NOVA SYSTEM ACTIVATED 🚀      ║
    ╠═════════════════════════════════════════╣
    ║ 🤖 Bot Name   : {bot.user.name}             
    ║ 🆔 Bot ID     : {bot.user.id}               
    ║ 📡 Discord.py : {discord.__version__}       
    ║ 💎 Premium    : Active (System Ready)   
    ╚═════════════════════════════════════════╝
    """)
    
    # স্ট্যাটাস সেট করা (Nova Style)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="Novaworld | /help"
        ),
        status=discord.Status.idle
    )

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

# ================= 4. টোকেন রান =================
# আপনার টোকেন এখানে সরাসরি দিন অথবা .env ফাইল ব্যবহার করুন
TOKEN = "YOUR_BOT_TOKEN_HERE" 

if __name__ == "__main__":
    try:
        # যদি এনভায়রনমেন্ট ভেরিয়েবল ব্যবহার করেন
        # bot.run(os.getenv('DISCORD_TOKEN'))
        
        # অথবা সরাসরি টোকেন দিয়ে রান করতে চাইলে:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Token Error: {e}")
