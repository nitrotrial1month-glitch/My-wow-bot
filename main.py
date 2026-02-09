import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from typing import Optional
import re

# Railway Variable থেকে টোকেন নেওয়া
TOKEN = os.getenv('DISCORD_TOKEN')

# এন্টিলিংক ডেটা (সাময়িকভাবে মেমোরিতে থাকবে)
anti_link_status = {
    "enabled": False, 
    "blocked_links": []
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # এটি স্ল্যাশ কমান্ডগুলো ডিসকর্ডের সাথে সিঙ্ক করবে
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - Online!')

# --- এন্টিলিংক ড্যাশবোর্ড ভিউ (Buttons) ---
class AntiLinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Enable/Disable Anti-Link", style=discord.ButtonStyle.primary)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_link_status["enabled"] = not anti_link_status["enabled"]
        status = "Enabled" if anti_link_status["enabled"] else "Disabled"
        await interaction.response.send_message(f"✅ Anti-Link is now **{status}**", ephemeral=True)

    @discord.ui.button(label="View Blocklist", style=discord.ButtonStyle.secondary)
    async def view_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        links = ", ".join(anti_link_status["blocked_links"]) if anti_link_status["blocked_links"] else "None"
        await interaction.response.send_message(f"🚫 Blocked links/keywords: `{links}`", ephemeral=True)

# --- ১. এন্টিলিংক ড্যাশবোর্ড কমান্ড ---
@bot.tree.command(name="antilink", description="Open Anti-Link Security Dashboard")
async def antilink(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Only Admins can use this!", ephemeral=True)
    
    embed = discord.Embed(
        title="🛡️ Anti-Link Security Dashboard",
        description="নিচের বাটন ব্যবহার করে এন্টি-লিংক কন্ট্রোল করুন।",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, view=AntiLinkView(), ephemeral=True)

# --- ২. লিংক ব্লক করার কমান্ড ---
@bot.tree.command(name="blocklink", description="Add a link or keyword to block")
@app_commands.describe(link="Example: discord.gg or .com")
async def blocklink(interaction: discord.Interaction, link: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ No permission!", ephemeral=True)
    
    link = link.lower()
    if link not in anti_link_status["blocked_links"]:
        anti_link_status["blocked_links"].append(link)
        await interaction.response.send_message(f"✅ `{link}` ব্লক লিস্টে যোগ করা হয়েছে।", ephemeral=True)
    else:
        await interaction.response.send_message("❌ এটি আগেই ব্লক লিস্টে আছে।", ephemeral=True)

# --- ৩. অন-মেসেজ ইভেন্ট (Anti-Link Logic) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # এন্টি-লিংক যদি এনাবল থাকে তবে চেক করবে
    if anti_link_status["enabled"]:
        for blocked in anti_link_status["blocked_links"]:
            if blocked in message.content.lower():
                try:
                    await message.delete()
                    await message.channel.send(f"🚫 {message.author.mention}, এখানে লিংক পাঠানো নিষেধ!", delete_after=5)
                    return 
                except:
                    pass

    await bot.process_commands(message)

# --- ৪. সিকিউরিটি কমান্ডস (Lock, Unlock, Clear) ---
@bot.tree.command(name="lock", description="Lock the channel")
async def lock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ No permission!", ephemeral=True)
    target = role if role else interaction.guild.default_role
    await interaction.channel.set_permissions(target, send_messages=False)
    await interaction.response.send_message(f"🔒 Locked for {target.name}")

@bot.tree.command(name="unlock", description="Unlock the channel")
async def unlock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ No permission!", ephemeral=True)
    target = role if role else interaction.guild.default_role
    await interaction.channel.set_permissions(target, send_messages=True)
    await interaction.response.send_message(f"🔓 Unlocked for {target.name}")

@bot.tree.command(name="clear", description="Delete messages")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ No permission!", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.")

# বট রান করা
bot.run(TOKEN)
