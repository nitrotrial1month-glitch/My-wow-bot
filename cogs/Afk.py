import discord
from discord import app_commands
from discord.ext import commands
import json
import os

AFK_FILE = 'afk_data.json'

# --- ডাটা লোড ও সেভ ফাংশন ---
def load_afk():
    if os.path.exists(AFK_FILE):
        with open(AFK_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_afk(data):
    with open(AFK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. ইভেন্ট: AFK ডিটেকশন ও রিমুভাল ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        
        afk_data = load_afk()
        user_id = str(message.author.id)

        # ১. যদি AFK ইউজার মেসেজ দেয় (AFK রিমুভ হবে)
        if user_id in afk_data:
            details = afk_data.pop(user_id)
            save_afk(afk_data)
            
            # নিকনেম থেকে [AFK] সরানো
            try:
                new_nick = message.author.display_name.replace("[AFK] ", "")
                await message.author.edit(nick=new_nick)
            except: pass
            
            await message.channel.send(f"Welcome back {message.author.mention}, I've removed your AFK!", delete_after=5)

        # ২. কেউ যদি AFK ইউজারকে মেনশন করে
        if message.mentions:
            for mention in message.mentions:
                m_id = str(mention.id)
                if m_id in afk_data:
                    reason = afk_data[m_id]
                    embed = discord.Embed(
                        description=f"💤 **{mention.display_name}** is currently AFK\n**Reason:** {reason}",
                        color=0x2b2d31
                    )
                    await message.reply(embed=embed, delete_after=10)

    # --- ২. স্লাস কমান্ড: AFK সেট করা ---
    @app_commands.command(name="afk", description="Set your AFK status")
    @app_commands.describe(reason="Why are you going away?")
    async def afk(self, interaction: discord.Interaction, reason: str = "I am busy"):
        afk_data = load_afk()
        afk_data[str(interaction.user.id)] = reason
        save_afk(afk_data)
        
        # নিকনেমে [AFK] যোগ করা
        try:
            await interaction.user.edit(nick=f"[AFK] {interaction.user.display_name}")
        except: pass
        
        await interaction.response.send_message(f"✅ {interaction.user.mention}, I've set your AFK: **{reason}**")

async def setup(bot):
    await bot.add_cog(AFK(bot))
      
