import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select
from easy_pil import Editor, load_image_async, Font
import os
# Import configuration logic from utils
from utils import load_config, save_config, get_theme_color

# --- 1. MODALS FOR INPUTS ---
class EditMessageModal(Modal, title="📝 Edit Welcome Message"):
    msg = TextInput(label="New Message", style=discord.TextStyle.paragraph, placeholder="Welcome {member} to {server}!", required=True, max_length=1000)
    
    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        config.setdefault("welcome_settings", {})["message"] = self.msg.value
        save_config(config)
        await interaction.response.send_message(f"✅ Message updated to:\n`{self.msg.value}`", ephemeral=True)

class BackgroundModal(Modal, title="🖼️ Set Background Image"):
    url = TextInput(label="Image URL (Static/GIF)", placeholder="https://imgur.com/...", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        config.setdefault("welcome_settings", {})["image_url"] = self.url.value
        save_config(config)
        await interaction.response.send_message(f"✅ Background updated!", ephemeral=True)

class ColorModal(Modal, title="🎨 Set Accent Color"):
    hex_code = TextInput(label="Hex Color Code", placeholder="#00ff00", required=True, max_length=7)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        try:
            # Validate Hex
            color_int = int(self.hex_code.value.replace("#", ""), 16)
            config.setdefault("welcome_settings", {})["accent_color"] = color_int
            save_config(config)
            await interaction.response.send_message(f"✅ Accent color set to `{self.hex_code.value}`", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Invalid Hex Code! Example: #ff0000", ephemeral=True)

# --- 2. MAIN DASHBOARD VIEW ---
class WelcomeDashboardView(View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.config = load_config().get("welcome_settings", {})

    # --- ROW 1: BASIC SETUP ---
    @discord.ui.button(label="Set Channel", style=discord.ButtonStyle.success, emoji="📢", row=0)
    async def set_channel(self, interaction: discord.Interaction, button: Button):
        # We use a channel select menu for this
        await interaction.response.send_message("👇 Select the channel below:", view=ChannelSelectView(), ephemeral=True)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.danger, emoji="🔄", row=0)
    async def disable_system(self, interaction: discord.Interaction, button: Button):
        config = load_config()
        config.setdefault("welcome_settings", {})["enabled"] = False
        save_config(config)
        await interaction.response.send_message("🔴 Welcome System **DISABLED**.", ephemeral=True)

    @discord.ui.button(label="Test Welcome", style=discord.ButtonStyle.secondary, emoji="🧪", row=0)
    async def test_welcome(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⏳ Generating test card...", ephemeral=True)
        cog = interaction.client.get_cog("WelcomeSystem")
        if cog:
            await cog.send_welcome(interaction.user, is_test=True, channel=interaction.channel)

    @discord.ui.button(label="View Config", style=discord.ButtonStyle.secondary, emoji="👁️", row=0)
    async def view_config(self, interaction: discord.Interaction, button: Button):
        c = load_config().get("welcome_settings", {})
        status = "🟢 ON" if c.get("enabled") else "🔴 OFF"
        ch = f"<#{c.get('channel_id')}>" if c.get('channel_id') else "Not Set"
        
        desc = (
            f"**Status:** {status}\n"
            f"**Channel:** {ch}\n"
            f"**Message:** `{c.get('message', 'Default')}`\n"
            f"**Image:** [Link]({c.get('image_url', 'Default')})\n"
            f"**Ping & Delete:** {'✅' if c.get('ping_delete') else '❌'}"
        )
        embed = discord.Embed(title="⚙️ Current Configuration", description=desc, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- ROW 2: CUSTOMIZATION ---
    @discord.ui.button(label="Edit Message", style=discord.ButtonStyle.primary, emoji="✏️", row=1)
    async def edit_msg(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(EditMessageModal())

    @discord.ui.button(label="Background", style=discord.ButtonStyle.primary, emoji="🖼️", row=1)
    async def set_bg(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(BackgroundModal())

    @discord.ui.button(label="View Placeholders", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
    async def placeholders(self, interaction: discord.Interaction, button: Button):
        desc = (
            "`{member}` - Mentions the user\n"
            "`{username}` - User's name\n"
            "`{server}` - Server name\n"
            "`{count}` - Member count"
        )
        await interaction.response.send_message(embed=discord.Embed(title="🧩 Placeholders", description=desc, color=discord.Color.teal()), ephemeral=True)

    @discord.ui.button(label="Reset All", style=discord.ButtonStyle.danger, emoji="🔁", row=1)
    async def reset_all(self, interaction: discord.Interaction, button: Button):
        config = load_config()
        config["welcome_settings"] = {} # Wipe settings
        save_config(config)
        await interaction.response.send_message("⚠️ All Welcome settings have been reset to default!", ephemeral=True)

    # --- ROW 3: ADVANCED ---
    @discord.ui.button(label="Font Color", style=discord.ButtonStyle.blurple, emoji="🎨", row=2)
    async def font_color(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ColorModal())

    @discord.ui.button(label="Ping & Delete", style=discord.ButtonStyle.primary, emoji="📌", row=2)
    async def ping_delete(self, interaction: discord.Interaction, button: Button):
        config = load_config()
        current = config.get("welcome_settings", {}).get("ping_delete", False)
        config.setdefault("welcome_settings", {})["ping_delete"] = not current
        save_config(config)
        state = "Enabled" if not current else "Disabled"
        await interaction.response.send_message(f"📌 Ping & Delete: **{state}**", ephemeral=True)

# --- 3. CHANNEL SELECT VIEW ---
class ChannelSelect(Select):
    def __init__(self):
        super().__init__(placeholder="Select a Channel...", channel_types=[discord.ChannelType.text])
    
    async def callback(self, interaction: discord.Interaction):
        config = load_config()
        config.setdefault("welcome_settings", {})["channel_id"] = self.values[0].id
        config["welcome_settings"]["enabled"] = True # Auto enable
        save_config(config)
        await interaction.response.send_message(f"✅ Welcome channel set to {self.values[0].mention} and System **ENABLED**!", ephemeral=True)

class ChannelSelectView(View):
    def __init__(self):
        super().__init__()
        self.add_item(ChannelSelect())

# ==========================================
# 4. MAIN SYSTEM COG
# ==========================================
class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def generate_card(self, member, bg_url, accent_color=None):
        # Default fallback
        if not bg_url: bg_url = "https://img.freepik.com/free-vector/abstract-blue-geometric-shapes-background_1035-17545.jpg"
        
        # Image Processing
        background = Editor(await load_image_async(bg_url)).resize((900, 400))
        profile_image = await load_image_async(member.display_avatar.url)
        profile = Editor(profile_image).resize((200, 200)).circle_image()
        
        poppins = Font.poppins(size=50, variant="bold")
        poppins_small = Font.poppins(size=30, variant="light")
        
        # Draw
        background.paste(profile, (350, 50))
        background.ellipse((350, 50), 200, 200, outline="white", stroke_width=5)
        
        # Text
        text_color = "white" # Default
        if accent_color: text_color = discord.Color(accent_color).to_rgb()

        background.text((450, 280), "WELCOME", color=text_color, font=poppins, align="center")
        background.text((450, 340), f"{member.name}", color="white", font=poppins_small, align="center")
        
        return discord.File(fp=background.image_bytes, filename="welcome.jpg")

    async def send_welcome(self, member, is_test=False, channel=None):
        config = load_config()
        ws = config.get("welcome_settings", {})
        
        # Validation
        if not is_test:
            if not ws.get("enabled") or not ws.get("channel_id"): return
            channel = member.guild.get_channel(ws["channel_id"])
            if not channel: return

        # Prepare Message
        msg_content = ws.get("message", "Welcome {member} to {server}!")
        msg_content = msg_content.format(
            member=member.mention, 
            username=member.name, 
            server=member.guild.name, 
            count=member.guild.member_count
        )

        # Generate Image
        bg_url = ws.get("image_url")
        accent = ws.get("accent_color")
        file = await self.generate_card(member, bg_url, accent)
        
        # Send
        try:
            # Ping & Delete Logic
            if ws.get("ping_delete") and not is_test:
                ping_msg = await channel.send(member.mention)
                await ping_msg.delete(delay=5)

            # Nova Style Embed
            color = get_theme_color(member.guild.id)
            embed = discord.Embed(description=msg_content, color=color)
            embed.set_image(url="attachment://welcome.jpg")
            embed.set_footer(text=f"Member #{member.guild.member_count}")

            await channel.send(file=file, embed=embed)
        except Exception as e:
            print(f"Welcome Error: {e}")

    # --- Listener ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_welcome(member)

    # --- SETUP COMMAND ---
    @app_commands.command(name="setup_welcome", description="🛠️ Open the Advanced Welcome Dashboard")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_welcome(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛠️ Welcome System Dashboard",
            description="Configure your welcome messages, images, and settings below using the interactive buttons.",
            color=discord.Color.dark_theme()
        )
        embed.add_field(name="Basic Setup", value="Set Channel, Enable/Disable, Test", inline=False)
        embed.add_field(name="Customization", value="Edit Message, Background, Colors", inline=False)
        embed.set_thumbnail(url=interaction.client.user.avatar.url)
        
        view = WelcomeDashboardView(interaction.client, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))
            
