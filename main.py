import discord
from discord.ext import commands
import json
import os
from typing import Optional

# ================= 1. ডাটাবাস/কনফিগ হেল্পার ফাংশন =================
CONFIG_FILE = 'config.json'
PREFIX_FILE = 'prefixes.json'

def load_config():
    """config.json ফাইল লোড করে এবং না থাকলে ডিফল্ট ডাটা তৈরি করে"""
    if not os.path.exists(CONFIG_FILE):
        default_data = {
            "anti_link": {"enabled": False, "blocked_list": []},
            "bad_words": [],
            "auto_role_id": None,
            "welcome": {"channel_id": None, "title": "Welcome!", "description": "Hi {member}!", "image_url": None, "color": 0x00ff00},
            "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "image_url": None, "color": 0xff0000}
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    """config.json এ ডাটা সেভ করার সেন্ট্রাল ফাংশন"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_prefix(bot, message):
    """সার্ভার অনুযায়ী প্রিফিক্স লোড করা"""
    try:
        with open(PREFIX_FILE, 'r') as f:
            prefixes = json.load(f)
        return prefixes.get(str(message.guild.id), "Wow")
    except:
        return "Wow"

# ================= 2. মেইন বট ক্লাস সেটআপ =================

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        
        super().__init__(
            command_prefix=get_prefix, 
            intents=intents,
            strip_after_prefix=True  # 'Wow cf' বা 'Wowcf' উভয়ই ডিটেক্ট করবে
        )
        
    async def setup_hook(self):
        """বট চালু হওয়ার সময় Cog এবং Views লোড করা"""
        
        # ১. টিকেট সিস্টেমের ভিউ রেজিস্টার করা (যাতে Interaction Failed না আসে)
        try:
            from cogs.ticket import TicketLaunch, TicketControl
            self.add_view(TicketLaunch())
            self.add_view(TicketControl()) 
            print("✅ Persistent Ticket Views Registered!")
        except Exception as e:
            print(f"⚠️ Ticket View Error: {e}")

        # ২. সমস্ত Cog (welcome, moderation, afk, give) লোড করা
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f"🚀 Loaded Cog: {filename}")
                    except Exception as e:
                        print(f"❌ Error Loading {filename}: {e}")
        
        # ৩. স্ল্যাশ কমান্ড সিঙ্ক করা
        await self.tree.sync()
        print("🛰️ Slash Commands Synced Successfully!")

# ================= 3. গ্লোবাল ইভেন্ট এবং রান =================

bot = MyBot()

@bot.event
async def on_ready():
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🟢 Logged in as: {bot.user.name}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"📡 Discord Version: {discord.__version__}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # config.json চেক করা
    load_config()
    print("📂 config.json is Ready and Detected!")

@bot.event
async def on_message(message):
    # বট নিজে নিজের মেসেজ রিপ্লাই দিবে না
    if message.author.bot:
        return
    
    # প্রিফিক্স কমান্ড প্রসেস করা
    await bot.process_commands(message)

# বটের রানার (Railway/Local এনভায়রনমেন্ট থেকে টোকেন নিবে)
TOKEN = os.getenv('DISCORD_TOKEN')

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: No DISCORD_TOKEN found in your environment variables!")
        
