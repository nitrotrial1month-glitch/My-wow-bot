import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from typing import Optional

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# সব ডেটা স্টোরেজ (Anti-Link + Welcome + Leave)
server_data = {
    "anti_link": {"enabled": False, "blocked": []},
    "welcome": {
        "channel_id": None,
        "title": "Welcome to our Server!",
        "description": "Welcome {member}!\n\n📜 Rules: <#ID>\n💬 Chat: <#ID>",
        "image_url": None,
        "color": 0x00ff00
    },
    "leave": {
        "channel_id": None,
        "title": "Goodbye from the Server!",
        "description": "{member} has left us. We will miss you!\n\n👋 Come back soon!",
        "image_url": None,
        "color": 0xff0000
    }
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # এটি Welcome এবং Leave ইভেন্টের জন্য অবশ্যই লাগবে
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - All Systems Active!')

# ================= WELCOME & LEAVE EVENTS =================

@bot.event
async def on_member_join(member):
    config = server_data["welcome"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            desc = config["description"].replace("{member}", member.mention)
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member #{member.guild.member_count}")
            await channel.send(content=f"HEY {member.mention}", embed=embed)

@bot.event
async def on_member_remove(member):
    config = server_data["leave"]
    if config["channel_id"]:
        channel = bot.get_channel(config["channel_id"])
        if channel:
            # মেম্বার চলে গেলে তাকে মেনশন করা যায় না, তাই শুধু নাম দেখানো হচ্ছে
            desc = config["description"].replace("{member}", f"**{member.name}**")
            embed = discord.Embed(title=config["title"], description=desc, color=config["color"])
            if config["image_url"]: embed.set_image(url=config["image_url"])
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="Goodbye!")
            await channel.send(embed=embed)

# ================= MODALS & DASHBOARDS =================

class WelcomeSetupModal(Modal, title="Customize Welcome Message"):
    title_input = TextInput(label="Title", placeholder="🌸 WELCOME 🌸")
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["welcome"]["description"])
    gif_input = TextInput(label="GIF URL", placeholder="Paste link here.", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        server_data["welcome"].update({"title": self.title_input.value, "description": self.desc_input.value, "image_url": self.gif_input.value})
        await interaction.response.send_message("✅ Welcome message updated!", ephemeral=True)

class LeaveSetupModal(Modal, title="Customize Leave Message"):
    title_input = TextInput(label="Title", placeholder="💔 GOODBYE 💔")
    desc_input = TextInput(label="Description", style=discord.TextStyle.paragraph, default=server_data["leave"]["description"])
    gif_input = TextInput(label="GIF URL", placeholder="Paste link here.", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        server_data["leave"].update({"title": self.title_input.value, "description": self.desc_input.value, "image_url": self.gif_input.value})
        await interaction.response.send_message("✅ Leave message updated!", ephemeral=True)

# ================= SLASH COMMANDS =================

@bot.tree.command(name="setup_welcome", description="Configure welcome system")
async def setup_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    server_data["welcome"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.success)
    async def cb(inter): await inter.response.send_modal(WelcomeSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Welcome channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="setup_leave", description="Configure leave system")
async def setup_leave(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    server_data["leave"]["channel_id"] = channel.id
    view = View(); btn = Button(label="Edit Content", style=discord.ButtonStyle.danger)
    async def cb(inter): await inter.response.send_modal(LeaveSetupModal())
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message(f"📍 Leave channel: {channel.mention}", view=view, ephemeral=True)

@bot.tree.command(name="antilink", description="Anti-Link Dashboard")
async def antilink(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator: return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    view = View(); btn = Button(label="Toggle Anti-Link", style=discord.ButtonStyle.primary)
    async def cb(inter):
        server_data["anti_link"]["enabled"] = not server_data["anti_link"]["enabled"]
        await inter.response.send_message(f"✅ Anti-Link: {'Enabled' if server_data['anti_link']['enabled'] else 'Disabled'}", ephemeral=True)
    btn.callback = cb; view.add_item(btn)
    await interaction.response.send_message("🛡️ Anti-Link Control", view=view, ephemeral=True)

@bot.tree.command(name="blocklink", description="Block a specific link")
async def blocklink(interaction: discord.Interaction, link: str):
    server_data["anti_link"]["blocked"].append(link.lower())
    await interaction.response.send_message(f"✅ `{link}` blocked.", ephemeral=True)

@bot.tree.command(name="lock", description="Lock channel")
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("🔒 Channel Locked.")

@bot.tree.command(name="unlock", description="Unlock channel")
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("🔓 Channel Unlocked.")

@bot.tree.command(name="clear", description="Clear messages")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Cleared {amount} messages.", ephemeral=True)

# ================= MESSAGE LOGIC =================

@bot.event
async def on_message(message):
    if message.author.bot: return
    if server_data["anti_link"]["enabled"]:
        for blocked in server_data["anti_link"]["blocked"]:
            if blocked in message.content.lower():
                try: await message.delete(); await message.channel.send(f"🚫 {message.author.mention}, no links!", delete_after=5); return
                except: pass
    await bot.process_commands(message)

bot.run(TOKEN)

@bot.event
async def on_message(message):
    if message.author.bot: return
    if server_data["anti_link"]["enabled"]:
        for blocked in server_data["anti_link"]["blocked"]:
            if blocked in message.content.lower():
                try: await message.delete(); await message.channel.send(f"🚫 {message.author.mention}, no links!", delete_after=5); return
                except: pass
    await bot.process_commands(message)

bot.run(TOKEN)
    await interaction.response.send_message(f"✅ `{link}` added to blocklist.", ephemeral=True)

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
