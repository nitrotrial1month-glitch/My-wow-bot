import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# --- ডাটাবাস ফাংশন ---
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {"welcome": {"enabled": False}}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- এডিট করার পপ-আপ ফর্ম (Modal) ---
class WelcomeEditModal(discord.ui.Modal, title='Welcome Message Editor'):
    title_input = discord.ui.TextInput(label='Title', placeholder='e.g. Welcome to Our Server', required=False)
    msg_input = discord.ui.TextInput(label='Message Body', style=discord.TextStyle.paragraph, placeholder='Use {member}, {server}, {count}', required=False)
    image_input = discord.ui.TextInput(label='GIF/Image URL', placeholder='Paste link here...', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if self.title_input.value: config["welcome"]["title"] = self.title_input.value
        if self.msg_input.value: config["welcome"]["description"] = self.msg_input.value
        if self.image_input.value: config["welcome"]["image_url"] = self.image_input.value
        
        save_config(config)
        await interaction.response.send_message("✅ Settings updated successfully!", ephemeral=True)

# --- ড্যাশবোর্ড ভিউ ---
class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Full Edit Message", style=discord.ButtonStyle.success, emoji="🛠️")
    async def edit_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WelcomeEditModal())

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. স্লাস কমান্ড: অন এবং চ্যানেল সেট (একসাথে) ---
    @app_commands.command(name="welcome_on", description="Enable welcome system and set channel")
    @app_commands.describe(channel="The channel where welcome messages will be sent")
    async def welcome_on(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        if "welcome" not in config: config["welcome"] = {}
        
        config["welcome"]["enabled"] = True
        config["welcome"]["channel_id"] = channel.id
        save_config(config)
        
        await interaction.response.send_message(f"✅ Welcome system is now **ON** and channel set to {channel.mention}")

    # --- ২. স্লাস কমান্ড: অফ ---
    @app_commands.command(name="welcome_off", description="Turn off the welcome system")
    async def welcome_off(self, interaction: discord.Interaction):
        config = load_config()
        config["welcome"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("❌ Welcome system has been **Disabled**.")

    # --- ৩. স্লাস কমান্ড: ড্যাশবোর্ড (এডিট করার জন্য) ---
    @app_commands.command(name="welcome_dashboard", description="Edit message, GIF, and titles")
    async def welcome_dashboard(self, interaction: discord.Interaction):
        config = load_config()
        w = config.get("welcome", {})
        
        embed = discord.Embed(title="🎨 Welcome Customizer Dashboard", color=0x5865F2)
        embed.add_field(name="Current Title", value=w.get("title", "Welcome!"), inline=False)
        embed.add_field(name="Current Channel", value=f"<#{w.get('channel_id')}>" if w.get('channel_id') else "Not Set", inline=True)
        embed.set_footer(text="Click the button below to edit everything!")
        
        if w.get("image_url"):
            embed.set_image(url=w.get("image_url"))
            
        await interaction.response.send_message(embed=embed, view=DashboardView())

    # --- জয়েন ইভেন্ট ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = load_config()
        w = config.get("welcome", {})
        
        if not w.get("enabled", False): return
        
        channel = self.bot.get_channel(int(w.get("channel_id", 0)))
        if channel:
            desc = w.get("description", "Welcome {member}!").replace("{member}", member.mention)
            desc = desc.replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
            
            embed = discord.Embed(title=w.get("title", "Welcome!"), description=desc, color=0x00ff00)
            if w.get("image_url"): embed.set_image(url=w.get("image_url"))
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await channel.send(content=f"Welcome {member.mention}!", embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
