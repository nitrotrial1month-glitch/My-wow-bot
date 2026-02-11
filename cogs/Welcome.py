import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# --- ডাটা লোড ও সেভ ফাংশন (যদি utils না থাকে তবে এখানেই থাকবে) ---
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- ড্যাশবোর্ডের জন্য মোডাল ও ভিউ ---
class WelcomeEditModal(discord.ui.Modal, title='Edit Welcome Settings'):
    title_input = discord.ui.TextInput(label='Welcome Title', placeholder='e.g. Welcome to Our Server!', required=False)
    msg_input = discord.ui.TextInput(label='Message Body', style=discord.TextStyle.paragraph, placeholder='Use {member}, {server}, {count}', required=False)
    image_input = discord.ui.TextInput(label='GIF/Image URL', placeholder='https://example.com/welcome.gif', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if "welcome" not in config: config["welcome"] = {}
        
        if self.title_input.value: config["welcome"]["title"] = self.title_input.value
        if self.msg_input.value: config["welcome"]["description"] = self.msg_input.value
        if self.image_input.value: config["welcome"]["image_url"] = self.image_input.value
        
        save_config(config)
        await interaction.response.send_message("✅ Welcome settings updated!", ephemeral=True)

class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.primary, emoji="📝")
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WelcomeEditModal())

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = load_config()
        w = config.get("welcome", {})
        
        if not w.get("enabled", True): return
        
        channel_id = w.get("channel_id")
        if channel_id:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                desc = w.get("description", "Welcome {member}!").replace("{member}", member.mention)
                desc = desc.replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
                
                embed = discord.Embed(title=w.get("title", "Welcome!"), description=desc, color=0x00ff00)
                if w.get("image_url"): embed.set_image(url=w.get("image_url"))
                embed.set_thumbnail(url=member.display_avatar.url)
                
                await channel.send(content=f"Hey {member.mention}!", embed=embed)

    # --- স্ল্যাশ কমান্ডস ---
    @app_commands.command(name="welcome_on", description="Enable welcome system")
    async def welcome_on(self, interaction: discord.Interaction):
        config = load_config()
        if "welcome" not in config: config["welcome"] = {}
        config["welcome"]["enabled"] = True
        save_config(config)
        await interaction.response.send_message("✅ Welcome system enabled!")

    @app_commands.command(name="welcome_off", description="Disable welcome system")
    async def welcome_off(self, interaction: discord.Interaction):
        config = load_config()
        if "welcome" not in config: config["welcome"] = {}
        config["welcome"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("✅ Welcome system disabled!")

    @app_commands.command(name="welcome_dashboard", description="Manage welcome settings")
    async def welcome_dashboard(self, interaction: discord.Interaction):
        config = load_config()
        w = config.get("welcome", {})
        
        embed = discord.Embed(title="🖼️ Welcome Dashboard", color=0x2b2d31)
        embed.add_field(name="Status", value="🟢 ON" if w.get("enabled", True) else "🔴 OFF")
        embed.add_field(name="Channel", value=f"<#{w.get('channel_id')}>" if w.get('channel_id') else "Not Set")
        
        await interaction.response.send_message(embed=embed, view=DashboardView())

async def setup(bot):
    await bot.add_cog(Welcome(bot))
        
