import os
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

# Railway Variable থেকে টোকেন নেওয়া
TOKEN = os.getenv('DISCORD_TOKEN')

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        # এখানে প্রিফিক্স '!' থাকলেও আমরা মূলত স্ল্যাশ কমান্ড ব্যবহার করছি
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # এটি স্ল্যাশ কমান্ডগুলো ডিসকর্ডের সাথে সিঙ্ক করবে
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is online and ready!')

# --- Slash Command: Lock ---
@bot.tree.command(name="lock", description="Locks the channel for a specific role or @everyone")
@app_commands.describe(role="The role to lock (defaults to @everyone)")
async def lock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Your don't have `Manage Channels` permission!", ephemeral=True)
        return

    target_role = role if role else interaction.guild.default_role
    await interaction.channel.set_permissions(target_role, send_messages=False)
    await interaction.response.send_message(f"🔒 Channel has been locked for: **{target_role.name}**")

# --- Slash Command: Unlock ---
@bot.tree.command(name="unlock", description="Unlocks the channel for a specific role or @everyone")
@app_commands.describe(role="The role to unlock (defaults to @everyone)")
async def unlock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ Your don't have `Manage Channels` permission!", ephemeral=True)
        return

    target_role = role if role else interaction.guild.default_role
    await interaction.channel.set_permissions(target_role, send_messages=True)
    await interaction.response.send_message(f"🔓 Channel has been unlocked for: **{target_role.name}**")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: No DISCORD_TOKEN found!")
