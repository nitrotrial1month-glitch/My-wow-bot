import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import Optional

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# সব ডেটা স্টোরেজ (Anti-Link + Welcome)
server_data = {
    "anti_link": {"enabled": False, "blocked": []},
    "welcome": {
        "channel_id": None,
        "title": "Welcome to our Server!",
        "description": "Welcome {member}, we are glad to have you here!",
        "image_url": None,
        "color": 0x00ff00
    }
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # ওয়েলকাম মেসেজ ও মেম্বার কমান্ডের জন্য জরুরি
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - All Systems Active!')

# ================= WELCOME SYSTEM =================

@bot.event
async def on_member_join(member):
    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            desc = config["description"].replace("{member}", member.mention)
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]:
                embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(content=f"Hey {member.mention}!", embed=embed)

class WelcomeSetupModal(Modal, title="Customize Welcome Message"):
    title_input = TextInput(label="Welcome Title", placeholder="Ex: Welcome to our home!")
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, placeholder="Use {member} to tag the user.")
    gif_input = TextInput(label="GIF or Image URL", placeholder="Paste your GIF link here.", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"]["title"] = self.title_input.value
        server_data["welcome"]["description"] = self.desc_input.value
        server_data["welcome"]["image_url"] = self.gif_input.value
        await interaction.response.send_message("✅ Welcome message customized!", ephemeral=True)

@bot.tree.command(name="setup_welcome", description="Configure the welcome system")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    server_data["welcome"]["channel_id"] = channel.id
    view = View()
    edit_btn = Button(label="Edit Content & GIF", style=discord.ButtonStyle.success)
    async def edit_callback(inter): await inter.response.send_modal(WelcomeSetupModal())
    edit_btn.callback = edit_callback
    view.add_item(edit_btn)
    await interaction.response.send_message(f"📍 Welcome channel set to {channel.mention}.", view=view, ephemeral=True)

# ================= ANTI-LINK SYSTEM =================

class AntiLinkView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Enable/Disable Anti-Link", style=discord.ButtonStyle.primary)
    async def toggle(self, interaction: discord.Interaction, button: Button):
        server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
        status = "Enabled" if server_data["anti_link"]["enabled"] else "Disabled"
        await interaction.response.send_message(f"✅ Anti-Link is now **{status}**", ephemeral=True)

@bot.tree.command(name="antilink", description="Open Anti-Link Security Dashboard")
async def antilink(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    embed = discord.Embed(title="🛡️ Security Dashboard", description="Manage Anti-Link settings.", color=discord.Color.red())
    await interaction.response.send_message(embed=embed, view=AntiLinkView(), ephemeral=True)

@bot.tree.command(name="blocklink", description="Add a link to blocklist")
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked"].append(link.lower())
    await interaction.response.send_message(f"✅ `{link}` added to blocklist.", ephemeral=True)

# ================= SECURITY & UTILITY =================

@bot.tree.command(name="lock", description="Lock the channel")
async def lock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
    target = role if role else interaction.guild.default_role
    await interaction.channel.set_permissions(target, send_messages=False)
    await interaction.response.send_message(f"🔒 Locked for {target.name}")

@bot.tree.command(name="unlock", description="Unlock the channel")
async def unlock(interaction: discord.Interaction, role: Optional[discord.Role] = None):
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

# ================= MESSAGE EVENT (Anti-Link Logic) =================

@bot.event
async def on_message(message):
    if message.author.bot: return
    if server_data["anti_link"]["enabled"]:
        for blocked in server_data["anti_link"]["blocked"]:
            if blocked in message.content.lower():
                try:
                    await message.delete()
                    await message.channel.send(f"🚫 {message.author.mention}, links are not allowed!", delete_after=5)
                    return
                except: pass
    await bot.process_commands(message)

bot.run(TOKEN)
