import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {"anti_link": {"enabled": False, "bypass_roles": [], "blocked_keywords": []}}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- এডিট করার পপ-আপ ফর্ম (Modal) ---
class AntiLinkEditModal(discord.ui.Modal, title='Anti-Link Configuration'):
    keywords = discord.ui.TextInput(
        label='Blocked Keywords/Links', 
        style=discord.TextStyle.paragraph,
        placeholder='e.g. discord.gg, bit.ly, youtube.com (comma separated)',
        required=False
    )
    banner_url = discord.ui.TextInput(
        label='Dashboard Banner URL', 
        placeholder='Paste image/gif link here...',
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        if self.keywords.value:
            config["anti_link"]["blocked_keywords"] = [k.strip() for k in self.keywords.value.split(',')]
        if self.banner_url.value:
            config["anti_link"]["image_url"] = self.banner_url.value
        
        save_config(config)
        await interaction.response.send_message("✅ Anti-Link settings updated!", ephemeral=True)

# --- ড্যাশবোর্ড ভিউ (Buttons) ---
class AntiLinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Blocklist & Image", style=discord.ButtonStyle.primary, emoji="🚫")
    async def edit_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AntiLinkEditModal())

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

    # --- ১. ইভেন্ট: লিংক ডিটেকশন ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        
        config = load_config()
        al = config.get("anti_link", {})
        
        if not al.get("enabled", False): return

        # বাইপাস রোল চেক (যদি ইউজারের কোনো রোল বাইপাস লিস্টে থাকে)
        user_roles = [role.id for role in message.author.roles]
        if any(role_id in al.get("bypass_roles", []) for role_id in user_roles) or message.author.guild_permissions.administrator:
            return

        # লিংক চেক
        found_links = re.findall(self.link_regex, message.content.lower())
        if found_links:
            blocked_keywords = al.get("blocked_keywords", [])
            
            # যদি ব্লকলিস্ট খালি থাকে তবে সব লিংকই ডিলিট হবে, নতুবা শুধু কিওয়ার্ড ম্যাচ করলে ডিলিট হবে
            should_delete = False
            if not blocked_keywords:
                should_delete = True
            else:
                for link in found_links:
                    if any(kw in link for kw in blocked_keywords):
                        should_delete = True
                        break

            if should_delete:
                try:
                    await message.delete()
                    await message.channel.send(f"⚠️ {message.author.mention}, links are not allowed here!", delete_after=5)
                except: pass

    # --- ২. স্ল্যাশ কমান্ড: অ্যান্টি-লিংক অন ---
    @app_commands.command(name="antilink_on", description="Enable anti-link protection")
    async def antilink_on(self, interaction: discord.Interaction):
        config = load_config()
        config["anti_link"]["enabled"] = True
        save_config(config)
        await interaction.response.send_message("✅ Anti-Link system is now **Enabled**.")

    # --- ৩. স্ল্যাশ কমান্ড: অ্যান্টি-লিংক অফ ---
    @app_commands.command(name="antilink_off", description="Disable anti-link protection")
    async def antilink_off(self, interaction: discord.Interaction):
        config = load_config()
        config["anti_link"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("❌ Anti-Link system is now **Disabled**.")

    # --- ৪. স্ল্যাশ কমান্ড: বাইপাস রোল সেট করা ---
    @app_commands.command(name="antilink_bypass", description="Add or remove a role from bypass list")
    async def antilink_bypass(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        bypass_list = config["anti_link"].get("bypass_roles", [])
        
        if role.id in bypass_list:
            bypass_list.remove(role.id)
            msg = f"✅ Role {role.mention} removed from bypass list."
        else:
            bypass_list.append(role.id)
            msg = f"✅ Role {role.mention} added to bypass list."
        
        config["anti_link"]["bypass_roles"] = bypass_list
        save_config(config)
        await interaction.response.send_message(msg)

    # --- ৫. স্ল্যাশ কমান্ড: ড্যাশবোর্ড ---
    @app_commands.command(name="antilink_dashboard", description="Full control over Anti-Link")
    async def antilink_dashboard(self, interaction: discord.Interaction):
        config = load_config()
        al = config.get("anti_link", {})
        
        embed = discord.Embed(title="🛡️ Anti-Link Control Center", color=0x2b2d31)
        embed.add_field(name="Status", value="🟢 ON" if al.get("enabled") else "🔴 OFF", inline=True)
        
        keywords = ", ".join(al.get("blocked_keywords", [])) if al.get("blocked_keywords") else "All Links"
        embed.add_field(name="Blocked Content", value=f"`{keywords}`", inline=False)
        
        roles = ", ".join([f"<@&{r}>" for r in al.get("bypass_roles", [])]) if al.get("bypass_roles") else "Only Admins"
        embed.add_field(name="Bypassed Roles", value=roles, inline=False)
        
        if al.get("image_url"):
            embed.set_image(url=al.get("image_url"))
            
        await interaction.response.send_message(embed=embed, view=AntiLinkView())

async def setup(bot):
    await bot.add_cog(AntiLink(bot))

