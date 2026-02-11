import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, save_config

# --- এডিট করার জন্য পপ-আপ ফর্ম (Modal) ---
class WelcomeEditModal(discord.ui.Modal, title='Edit Welcome Settings'):
    title_input = discord.ui.TextInput(label='Welcome Title', placeholder='e.g. Welcome to Our Server!', required=False)
    msg_input = discord.ui.TextInput(label='Message', style=discord.TextStyle.paragraph, placeholder='Use {member}, {server}, {count}', required=False)
    image_input = discord.ui.TextInput(label='GIF/Image URL', placeholder='https://example.com/welcome.gif', required=False)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if self.title_input.value: config["welcome"]["title"] = self.title_input.value
        if self.msg_input.value: config["welcome"]["description"] = self.msg_input.value
        if self.image_input.value: config["welcome"]["image_url"] = self.image_input.value
        
        save_config(config)
        await interaction.response.send_message("✅ Welcome settings updated successfully!", ephemeral=True)

# --- ড্যাশবোর্ডের বাটন ইন্টারফেস ---
class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Content", style=discord.ButtonStyle.primary, emoji="📝")
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WelcomeEditModal())

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ড্যাশবোর্ড আপডেট করার লজিক
        await interaction.response.edit_message(embed=self.create_embed())

    def create_embed(self):
        config = load_config()
        w = config.get("welcome", {})
        embed = discord.Embed(title="🖼️ Welcome Dashboard", color=0x2b2d31)
        embed.add_field(name="Status", value="🟢 ON" if w.get("enabled") else "🔴 OFF", inline=True)
        embed.add_field(name="Channel", value=f"<#{w.get('channel_id')}>" if w.get('channel_id') else "Not Set", inline=True)
        embed.add_field(name="Title", value=w.get("title", "Welcome!"), inline=False)
        if w.get("image_url"): embed.set_image(url=w.get("image_url"))
        return embed

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- ১. স্লাস কমান্ড: ওয়েলকাম অন (On) ---
    @app_commands.command(name="welcome_on", description="Enable the welcome system")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_on(self, interaction: discord.Interaction):
        config = load_config()
        config["welcome"]["enabled"] = True
        save_config(config)
        await interaction.response.send_message("✅ Welcome system has been **Enabled**.")

    # --- ২. স্লাস কমান্ড: ওয়েলকাম অফ (Off) ---
    @app_commands.command(name="welcome_off", description="Disable the welcome system")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_off(self, interaction: discord.Interaction):
        config = load_config()
        config["welcome"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("✅ Welcome system has been **Disabled**.")

    # --- ৩. স্লাস কমান্ড: ড্যাশবোর্ড (Dashboard) ---
    @app_commands.command(name="welcome_dashboard", description="Full control over welcome settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_dashboard(self, interaction: discord.Interaction):
        view = DashboardView()
        await interaction.response.send_message(embed=view.create_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
    config = load_config()
        config["welcome"]["image_url"] = url
        save_config(config)
        await ctx.send(f"✅ Welcome image updated!")

    @setwelcome.command(name="role", description="Set auto-role")
    async def set_autorole(self, ctx, role: discord.Role):
        config = load_config()
        config["auto_role_id"] = role.id
        save_config(config)
        await ctx.send(f"✅ Auto-Role set to **{role.name}**")

    @commands.hybrid_command(name="testwelcome")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        await self.on_member_join(ctx.author)
        await ctx.send("✅ Test message sent!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
              
