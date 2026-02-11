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
    return {"leave": {"enabled": False}}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- এডিট করার পপ-আপ ফর্ম (Modal) ---
class LeaveEditModal(discord.ui.Modal, title='Leave Message Editor'):
    title_input = discord.ui.TextInput(label='Title', placeholder='e.g. Goodbye from the Server', required=False)
    msg_input = discord.ui.TextInput(label='Message Body', style=discord.TextStyle.paragraph, placeholder='Use {member}, {server}, {count}', required=False)
    image_input = discord.ui.TextInput(label='GIF/Image URL', placeholder='Paste link here...', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if "leave" not in config: config["leave"] = {}
        
        if self.title_input.value: config["leave"]["title"] = self.title_input.value
        if self.msg_input.value: config["leave"]["description"] = self.msg_input.value
        if self.image_input.value: config["leave"]["image_url"] = self.image_input.value
        
        save_config(config)
        await interaction.response.send_message("✅ Leave settings updated successfully!", ephemeral=True)

# --- ড্যাশবোর্ড ভিউ ---
class LeaveDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Leave Message", style=discord.ButtonStyle.danger, emoji="⚙️")
    async def edit_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LeaveEditModal())

class Leave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. স্লাস কমান্ড: লিভ অন এবং চ্যানেল সেট ---
    @app_commands.command(name="leave_on", description="Enable leave system and set channel")
    @app_commands.describe(channel="The channel where leave messages will be sent")
    async def leave_on(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        if "leave" not in config: config["leave"] = {}
        
        config["leave"]["enabled"] = True
        config["leave"]["channel_id"] = channel.id
        save_config(config)
        
        await interaction.response.send_message(f"✅ Leave system is now **ON** and channel set to {channel.mention}")

    # --- ২. স্লাস কমান্ড: লিভ অফ ---
    @app_commands.command(name="leave_off", description="Turn off the leave system")
    async def leave_off(self, interaction: discord.Interaction):
        config = load_config()
        config["leave"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("❌ Leave system has been **Disabled**.")

    # --- ৩. স্লাস কমান্ড: লিভ ড্যাশবোর্ড ---
    @app_commands.command(name="leave_dashboard", description="Edit leave message, GIF, and titles")
    async def leave_dashboard(self, interaction: discord.Interaction):
        config = load_config()
        l = config.get("leave", {})
        
        embed = discord.Embed(title="👋 Leave Customizer Dashboard", color=0xFF4B4B)
        embed.add_field(name="Current Title", value=l.get("title", "Goodbye!"), inline=False)
        embed.add_field(name="Status", value="🟢 ON" if l.get("enabled") else "🔴 OFF", inline=True)
        embed.add_field(name="Channel", value=f"<#{l.get('channel_id')}>" if l.get('channel_id') else "Not Set", inline=True)
        
        if l.get("image_url"):
            embed.set_image(url=l.get("image_url"))
            
        await interaction.response.send_message(embed=embed, view=LeaveDashboardView())

    # --- মেম্বার লিভ ইভেন্ট ---
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        config = load_config()
        l = config.get("leave", {})
        
        if not l.get("enabled", False): return
        
        channel = self.bot.get_channel(int(l.get("channel_id", 0)))
        if channel:
            desc = l.get("description", "{member} just left the server.").replace("{member}", member.name)
            desc = desc.replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
            
            embed = discord.Embed(title=l.get("title", "Goodbye!"), description=desc, color=0xFF0000)
            if l.get("image_url"): embed.set_image(url=l.get("image_url"))
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leave(bot))
          
