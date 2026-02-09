import os
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

# Railway Variable
TOKEN = os.getenv('DISCORD_TOKEN')

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # এটি মেম্বার কিক/ব্যান করার জন্য প্রয়োজন
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - Security Mode Active!')

# --- ১. Lock Command ---
@bot.tree.command(name="lock", description="Locks the channel")
@app_commands.describe(role="Role to lock (defaults to @everyone)")
async def lock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ No permission!", ephemeral=True)
    target_role = role if role else interaction.guild.default_role
    await interaction.channel.set_permissions(target_role, send_messages=False)
    await interaction.response.send_message(f"🔒 Locked for **{target_role.name}**")

# --- ২. Unlock Command ---
@bot.tree.command(name="unlock", description="Unlocks the channel")
@app_commands.describe(role="Role to unlock (defaults to @everyone)")
async def unlock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    if not interaction.user.guild_permissions.manage_channels:
        return await interaction.response.send_message("❌ No permission!", ephemeral=True)
    target_role = role if role else interaction.guild.default_role
    await interaction.channel.set_permissions(target_role, send_messages=True)
    await interaction.response.send_message(f"🔓 Unlocked for **{target_role.name}**")

# --- ৩. Kick Command (Security) ---
@bot.tree.command(name="kick", description="Kicks a member from the server")
@app_commands.describe(member="Member to kick", reason="Reason for kicking")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("❌ You don't have `Kick Members` permission!", ephemeral=True)
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 **{member.name}** has been kicked. Reason: {reason}")

# --- ৪. Ban Command (Security) ---
@bot.tree.command(name="ban", description="Bans a member from the server")
@app_commands.describe(member="Member to ban", reason="Reason for banning")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("❌ You don't have `Ban Members` permission!", ephemeral=True)
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 **{member.name}** has been banned. Reason: {reason}")

# --- ৫. Clear/Purge Command ---
@bot.tree.command(name="clear", description="Deletes a specific number of messages")
@app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ You don't have `Manage Messages` permission!", ephemeral=True)
    if amount < 1:
        return await interaction.response.send_message("❌ Please provide a number greater than 0!", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True) # টাইমআউট এড়াতে
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted **{len(deleted)}** messages.")

if __name__ == "__main__":
    bot.run(TOKEN)
