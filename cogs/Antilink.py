import discord
from discord import app_commands
from discord.ext import commands
import re
import datetime
# utils থেকে প্রিমিয়াম লজিক এবং কনফিগ ইমপোর্ট
from utils import load_config, save_config, get_theme_color

# --- Helper Function: Premium Check ---
def is_premium(interaction: discord.Interaction):
    """চেক করবে সার্ভারটি Premium (Gold) কি না"""
    color = get_theme_color(interaction.guild.id)
    return color == discord.Color.gold()

# --- Modal: Dashboard Edit (Premium Only) ---
class AntiLinkEditModal(discord.ui.Modal, title='⚙️ Configure Anti-Link (Premium)'):
    keywords = discord.ui.TextInput(
        label='Blocked Domains (Comma Separated)', 
        style=discord.TextStyle.paragraph,
        placeholder='example: discord.gg, bit.ly, youtube.com',
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

        # ডোমেইন লিস্ট সেভ করা
        if self.keywords.value:
            keywords_list = [k.strip().lower() for k in self.keywords.value.split(',')]
            config["anti_link"]["blocked_list"] = keywords_list
        
        # ব্যানার ইমেজ সেভ করা
        if self.banner_url.value:
            config["anti_link"]["image_url"] = self.banner_url.value
        
        save_config(config)
        await interaction.response.send_message("✅ **Anti-Link সেটিংস সফলভাবে আপডেট করা হয়েছে!**", ephemeral=True)

# --- View: Dashboard Buttons ---
class AntiLinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Config", style=discord.ButtonStyle.primary, emoji="🛠️")
    async def edit_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        # এডিট করার আগে আবার প্রিমিয়াম চেক
        if not is_premium(interaction):
            await interaction.response.send_message("❌ **অ্যাক্সেস ডিনাইড!** এটি শুধুমাত্র প্রিমিয়াম সার্ভারের জন্য।", ephemeral=True)
            return
        await interaction.response.send_modal(AntiLinkEditModal())

# --- Main AntiLink System ---
class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # সব ধরণের লিঙ্ক ডিটেক্ট করার জন্য Regex
        self.link_regex = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        
        config = load_config()
        al = config.get("anti_link", {})
        
        # যদি অ্যান্টি-লিঙ্ক বন্ধ থাকে
        if not al.get("enabled", False): return

        # অ্যাডমিন ও বাইপাস রোল চেক
        if message.author.guild_permissions.administrator: return
        user_roles = [role.id for role in message.author.roles]
        if any(role_id in al.get("bypass_roles", []) for role_id in user_roles): return

        # লিঙ্ক ডিটেকশন লজিক
        found_links = re.findall(self.link_regex, message.content.lower())
        if found_links:
            blocked_list = al.get("blocked_list", [])
            should_delete = False
            
            if not blocked_list:
                should_delete = True # লিস্ট খালি থাকলে সব লিঙ্ক ডিলিট হবে
            else:
                for link in found_links:
                    if any(word in link for word in blocked_list):
                        should_delete = True
                        break

            if should_delete:
                try:
                    # ১. মেসেজ ডিলিট করা
                    await message.delete()

                    # ২. স্টাইলিশ ডিলিট মেসেজ (Nova/Falcon Style)
                    color = get_theme_color(message.guild.id)
                    embed = discord.Embed(
                        description=(
                            f"### 🛡️ **Link Protection Active**\n"
                            f"────────────────────\n"
                            f"⚠️ {message.author.mention}, **Links are not allowed here!**\n"
                            f"```Security Level: High | Message Removed```\n"
                            f"────────────────────"
                        ),
                        color=color
                    )
                    await message.channel.send(embed=embed, delete_after=7)
                except: pass

    # --- ১. অন/অফ কমান্ড (Stylish Nova Style) ---
    @app_commands.command(name="antilink_on", description="Enable anti-link protection (Free)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_on(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config: config["anti_link"] = {}
        config["anti_link"]["enabled"] = True
        save_config(config)

        color = get_theme_color(interaction.guild.id)
        embed = discord.Embed(
            title="🛡️ WOW LINK PROTECTION",
            description=(
                "**Thanks for activating Anti-Link!**\n\n"
                "```Server security has improved.```\n"
                "*No one is allowed to send any type of links here.*\n\n"
                "✅ **Status:** Active\n"
                "🚫 **Anti Spam:** Enabled\n"
                "🛡️ **Security:** High"
            ),
            color=color
        )
        embed.set_footer(text=f"Wow System | {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="antilink_off", description="Disable anti-link protection (Free)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_off(self, interaction: discord.Interaction):
        config = load_config()
        if "anti_link" not in config: config["anti_link"] = {}
        config["anti_link"]["enabled"] = False
        save_config(config)

        embed = discord.Embed(
            description="❌ **Anti-Link protection has been disabled.**\nUsers can now post links in this server.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    # --- ২. বাইপাস রোল (Premium Only) ---
    @app_commands.command(name="antilink_bypass", description="[PREMIUM] Set roles that can send links")
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

    # --- ৩. ড্যাশবোর্ড (Premium View) ---
    @app_commands.command(name="antilink_dashboard", description="[PREMIUM] Configure settings & banner")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def antilink_dashboard(self, interaction: discord.Interaction):
        color = get_theme_color(interaction.guild.id)
        config = load_config()
        al = config.get("anti_link", {})
        
        status = "🟢 Enabled" if al.get("enabled") else "🔴 Disabled"
        sub_type = "✨ Premium Activated" if is_premium(interaction) else "🟦 Free Server"
        
        embed = discord.Embed(title="🛡️ Anti-Link Dashboard", color=color)
        embed.description = f"**Current Status:** {status}\n**Subscription:** {sub_type}"
        
        embed.add_field(name="🚫 Blocked Filters", value=f"{len(al.get('blocked_list', []))} domains", inline=True)
        embed.add_field(name="🔓 Whitelisted", value=f"{len(al.get('bypass_roles', []))} roles", inline=True)
        
        # প্রিমিয়াম সার্ভারে ইমেজ দেখাবে
        if is_premium(interaction) and al.get("image_url"):
            embed.set_image(url=al["image_url"])
            
        await interaction.response.send_message(embed=embed, view=AntiLinkView())

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
                
