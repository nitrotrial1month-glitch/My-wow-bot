import discord
from discord import app_commands
from discord.ext import commands
import re
from utils import load_config, save_config, check_advanced_premium

# --- Helper Function: Tier Check ---
def is_pro_or_ultra(interaction: discord.Interaction):
    """
    চেক করবে ইউজার বা সার্ভারের টিয়ার 'pro' বা 'ultra' কিনা।
    Basic বা Free হলে False রিটার্ন করবে।
    """
    # ১. ইউজার চেক
    user_status = check_advanced_premium(interaction.user.id)
    if user_status["active"] and user_status["tier"] in ["pro", "ultra"]:
        return True

    # ২. সার্ভার চেক
    server_status = check_advanced_premium(None, interaction.guild.id)
    if server_status["active"] and server_status["tier"] in ["pro", "ultra"]:
        return True

    return False

# --- Modal: Dashboard Edit ---
class AntiLinkEditModal(discord.ui.Modal, title='⚙️ Configure Anti-Link'):
    # এই টেক্সট ইনপুট গুলোর সিনট্যাক্স ঠিক করা হয়েছে
    keywords = discord.ui.TextInput(
        label='Blocked Domains (Comma Separated)', 
        style=discord.TextStyle.paragraph,
        placeholder='example: discord.gg, bit.ly, steamcommunity.com',
        required=False
    )
    banner_url = discord.ui.TextInput(
        label='Dashboard Banner URL', 
        placeholder='https://image.url/banner.png',
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config:
            config["anti_link"] = {}

        # ডাটা সেভ করা
        if self.keywords.value:
            # কমা দিয়ে আলাদা করে লিস্ট বানানো
            keywords_list = [k.strip().lower() for k in self.keywords.value.split(',')]
            config["anti_link"]["blocked_list"] = keywords_list
        
        if self.banner_url.value:
            config["anti_link"]["image_url"] = self.banner_url.value
        
        save_config(config)
        await interaction.response.send_message("✅ **Anti-Link Configuration Updated!**", ephemeral=True)

# --- View: Dashboard Buttons ---
class AntiLinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Config", style=discord.ButtonStyle.primary, emoji="🛠️")
    async def edit_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        # বাটন চাপলে আবার টিয়ার চেক করা হবে
        if not is_pro_or_ultra(interaction):
            await interaction.response.send_message(
                "❌ **Access Denied!**\nEditing the dashboard is restricted to **Pro** & **Ultra** tiers.\nUse `/buy_premium` to upgrade.", 
                ephemeral=True
            )
            return # রিটার্ন নিশ্চিত করা হলো

        await interaction.response.send_modal(AntiLinkEditModal())

# --- Main Cog ---
class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # সব ধরণের লিঙ্ক ধরার জন্য Regex
        self.link_regex = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        config = load_config()
        al = config.get("anti_link", {})
        
        # যদি অ্যান্টি-লিঙ্ক বন্ধ থাকে
        if not al.get("enabled", False):
            return

        # বাইপাস চেক (Admin or Whitelisted Roles)
        if message.author.guild_permissions.administrator:
            return
            
        user_roles = [role.id for role in message.author.roles]
        if any(role_id in al.get("bypass_roles", []) for role_id in user_roles):
            return

        # লিঙ্ক ডিটেকশন
        found_links = re.findall(self.link_regex, message.content.lower())
        if found_links:
            blocked_list = al.get("blocked_list", [])
            
            # যদি ব্লক লিস্ট খালি থাকে, সব লিঙ্ক ডিলিট করবে
            should_delete = False
            if not blocked_list:
                should_delete = True
            else:
                # ব্লক লিস্টে থাকা শব্দ লিঙ্কে আছে কিনা চেক
                for link in found_links:
                    if any(blocked_word in link for blocked_word in blocked_list):
                        should_delete = True
                        break

            if should_delete:
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, posting links is disabled!", delete_after=5)
                except:
                    pass

    # --- ১. অন/অফ কমান্ড (সবার জন্য ফ্রি) ---
    @app_commands.command(name="antilink_on", description="Enable anti-link protection (Free)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_on(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config:
            config["anti_link"] = {}
        
        config["anti_link"]["enabled"] = True
        save_config(config)
        await interaction.response.send_message("✅ **Anti-Link is now ENABLED.**")

    @app_commands.command(name="antilink_off", description="Disable anti-link protection (Free)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_off(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config:
            config["anti_link"] = {}

        config["anti_link"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("❌ **Anti-Link is now DISABLED.**")

    # --- ২. বাইপাস রোল সেট (Pro/Ultra Only) ---
    @app_commands.command(name="antilink_bypass", description="[PRO/ULTRA] Add/Remove bypass roles")
    @app_commands.describe(role="The role to bypass anti-link")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_bypass(self, interaction: discord.Interaction, role: discord.Role):
        # টিয়ার চেক
        if not is_pro_or_ultra(interaction):
            await interaction.response.send_message(
                "💎 This feature requires **Pro** or **Ultra** premium.\nBasic users cannot use bypass roles.", 
                ephemeral=True
            )
            return

        config = load_config()
        if "anti_link" not in config: config["anti_link"] = {}
        if "bypass_roles" not in config["anti_link"]: config["anti_link"]["bypass_roles"] = []
        
        bypass_list = config["anti_link"]["bypass_roles"]
        
        if role.id in bypass_list:
            bypass_list.remove(role.id)
            msg = f"⛔ Role **{role.name}** removed from bypass list."
        else:
            bypass_list.append(role.id)
            msg = f"✅ Role **{role.name}** added to bypass list."
        
        save_config(config)
        await interaction.response.send_message(msg)

    # --- ৩. ড্যাশবোর্ড (Pro/Ultra Only) ---
    @app_commands.command(name="antilink_dashboard", description="[PRO/ULTRA] Configure Blocked Links & Image")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_dashboard(self, interaction: discord.Interaction):
        # টিয়ার চেক
        if not is_pro_or_ultra(interaction):
            await interaction.response.send_message(
                "💎 **Premium Feature!**\nDashboard access is limited to **Pro** and **Ultra** users only.", 
                ephemeral=True
            )
            return

        config = load_config()
        al = config.get("anti_link", {})
        
        status = "🟢 Enabled" if al.get("enabled") else "🔴 Disabled"
        blocked_count = len(al.get("blocked_list", []))
        bypass_count = len(al.get("bypass_roles", []))
        
        embed = discord.Embed(title="🛡️ Anti-Link Dashboard", color=discord.Color.blue())
        embed.description = f"**Status:** {status}\n**Tier Access:** ✅ Pro/Ultra Authorized"
        
        embed.add_field(name="🚫 Blocked Keywords", value=f"{blocked_count} active filters", inline=True)
        embed.add_field(name="🔓 Bypass Roles", value=f"{bypass_count} roles", inline=True)
        
        # যদি কাস্টম ইমেজ সেট করা থাকে
        if "image_url" in al and al["image_url"]:
            embed.set_image(url=al["image_url"])
            
        await interaction.response.send_message(embed=embed, view=AntiLinkView())

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
                    
