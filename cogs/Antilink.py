import discord
from discord import app_commands
from discord.ext import commands
import re
# utils থেকে প্রয়োজনীয় ফাংশন ইমপোর্ট
from utils import load_config, save_config, get_theme_color

# --- Helper Function: Premium Check ---
def is_premium(interaction: discord.Interaction):
    """চেক করবে সার্ভারটি Premium কি না"""
    color = get_theme_color(interaction.guild.id)
    return color == discord.Color.gold()

# --- Modal: Dashboard Edit ---
class AntiLinkEditModal(discord.ui.Modal, title='⚙️ Configure Anti-Link (Premium)'):
    keywords = discord.ui.TextInput(
        label='Blocked Domains (Comma Separated)', 
        style=discord.TextStyle.paragraph,
        placeholder='example: discord.gg, bit.ly',
        required=False
    )
    banner_url = discord.ui.TextInput(
        label='Dashboard Banner URL', 
        placeholder='https://image.url/banner.png',
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config: config["anti_link"] = {}

        if self.keywords.value:
            keywords_list = [k.strip().lower() for k in self.keywords.value.split(',')]
            config["anti_link"]["blocked_list"] = keywords_list
        
        if self.banner_url.value:
            config["anti_link"]["image_url"] = self.banner_url.value
        
        save_config(config)
        await interaction.response.send_message("✅ **Anti-Link সেটিংস আপডেট করা হয়েছে!**", ephemeral=True)

# --- View: Dashboard Buttons ---
class AntiLinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Config", style=discord.ButtonStyle.primary, emoji="🛠️")
    async def edit_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_premium(interaction):
            await interaction.response.send_message("❌ **অ্যাক্সেস ডিনাইড!** এটি শুধুমাত্র প্রিমিয়াম সার্ভারের জন্য।", ephemeral=True)
            return
        await interaction.response.send_modal(AntiLinkEditModal())

# --- Main Cog ---
class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_regex = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        
        config = load_config()
        al = config.get("anti_link", {})
        if not al.get("enabled", False): return

        # Admin ও Bypass Roles চেক
        if message.author.guild_permissions.administrator: return
        user_roles = [role.id for role in message.author.roles]
        if any(role_id in al.get("bypass_roles", []) for role_id in user_roles): return

        found_links = re.findall(self.link_regex, message.content.lower())
        if found_links:
            blocked_list = al.get("blocked_list", [])
            should_delete = False
            
            if not blocked_list:
                should_delete = True # লিস্ট খালি থাকলে সব লিঙ্ক ডিলিট
            else:
                for link in found_links:
                    if any(word in link for word in blocked_list):
                        should_delete = True
                        break

            if should_delete:
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, লিঙ্ক শেয়ার করা নিষেধ!", delete_after=5)
                except: pass

    # --- ১. অন/অফ কমান্ড ---
    @app_commands.command(name="antilink_on", description="Enable anti-link protection (Free)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_on(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config: config["anti_link"] = {}
        config["anti_link"]["enabled"] = True
        save_config(config)
        await interaction.response.send_message("✅ **Anti-Link এখন সচল (Enabled)।**")

    @app_commands.command(name="antilink_off", description="Disable anti-link protection (Free)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_off(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config: config["anti_link"] = {}
        config["anti_link"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("❌ **Anti-Link এখন বন্ধ (Disabled)।**")

    # --- ২. বাইপাস রোল সেট (Premium Only) ---
    @app_commands.command(name="antilink_bypass", description="[PREMIUM] Add/Remove bypass roles")
    @app_commands.describe(role="The role to bypass anti-link")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_bypass(self, interaction: discord.Interaction, role: discord.Role):
        if not is_premium(interaction):
            await interaction.response.send_message("💎 এই ফিচারটি শুধুমাত্র **Premium Server**-এর জন্য।", ephemeral=True)
            return

        config = load_config()
        if "anti_link" not in config: config["anti_link"] = {}
        if "bypass_roles" not in config["anti_link"]: config["anti_link"]["bypass_roles"] = []
        
        bypass_list = config["anti_link"]["bypass_roles"]
        if role.id in bypass_list:
            bypass_list.remove(role.id)
            msg = f"⛔ রোল **{role.name}** বাইপাস লিস্ট থেকে সরানো হয়েছে।"
        else:
            bypass_list.append(role.id)
            msg = f"✅ রোল **{role.name}** বাইপাস লিস্টে যোগ করা হয়েছে।"
        
        save_config(config)
        await interaction.response.send_message(msg)

    # --- ৩. ড্যাশবোর্ড (Premium Access) ---
    @app_commands.command(name="antilink_dashboard", description="[PREMIUM] Configure settings & banner")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_dashboard(self, interaction: discord.Interaction):
        color = get_theme_color(interaction.guild.id)
        config = load_config()
        al = config.get("anti_link", {})
        
        status = "🟢 Enabled" if al.get("enabled") else "🔴 Disabled"
        is_prem = "✅ Premium Server" if is_premium(interaction) else "❌ Free Server"
        
        embed = discord.Embed(title="🛡️ Anti-Link Dashboard", color=color)
        embed.description = f"**Status:** {status}\n**Subscription:** {is_prem}"
        
        embed.add_field(name="🚫 Blocked Keywords", value=f"{len(al.get('blocked_list', []))} filters", inline=True)
        embed.add_field(name="🔓 Bypass Roles", value=f"{len(al.get('bypass_roles', []))} roles", inline=True)
        
        if is_premium(interaction) and al.get("image_url"):
            embed.set_image(url=al["image_url"])
            
        await interaction.response.send_message(embed=embed, view=AntiLinkView())

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
    
