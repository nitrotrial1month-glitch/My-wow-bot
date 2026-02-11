import discord
from discord import app_commands
from discord.ext import commands
import re
from utils import load_config, save_config, is_user_premium # শুধুমাত্র utils থেকে ইম্পোর্ট করুন

class AntiLinkEditModal(discord.ui.Modal, title='Anti-Link Configuration'):
    keywords = discord.ui.TextInput(
        label='Blocked Keywords/Links', 
        style=discord.TextStyle.paragraph,
        placeholder='e.g. discord.gg, bit.ly (comma separated)',
        required=False
    )
    banner_url = discord.ui.TextInput(
        label='Dashboard Banner URL', 
        placeholder='Paste image/gif link here...',
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        # utils.py এর ডিফল্ট ফরম্যাট অনুযায়ী নাম ঠিক রাখা হলো
        if self.keywords.value:
            config["anti_link"]["blocked_list"] = [k.strip() for k in self.keywords.value.split(',')]
        if self.banner_url.value:
            config["anti_link"]["image_url"] = self.banner_url.value
        
        save_config(config)
        await interaction.response.send_message("✅ Anti-Link settings updated!", ephemeral=True)

class AntiLinkView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Edit Blocklist & Image", style=discord.ButtonStyle.primary, emoji="🚫")
    async def edit_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        # প্রিমিয়াম চেক
        if not is_user_premium(interaction.user.id):
            return await interaction.response.send_message("⭐ This is a **Premium Feature**.", ephemeral=True)
            
        await interaction.response.send_modal(AntiLinkEditModal())

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        config = load_config()
        al = config.get("anti_link", {})
        if not al.get("enabled", False): return

        # বাইপাস চেক
        user_roles = [role.id for role in message.author.roles]
        if any(role_id in al.get("bypass_roles", []) for role_id in user_roles) or message.author.guild_permissions.administrator:
            return

        found_links = re.findall(self.link_regex, message.content.lower())
        if found_links:
            # utils.py এর blocked_list ব্যবহার করা হলো
            blocked_keywords = al.get("blocked_list", [])
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
                    await message.channel.send(f"⚠️ {message.author.mention}, links are not allowed!", delete_after=5)
                except: pass

    @app_commands.command(name="antilink_on", description="Enable anti-link protection")
    async def antilink_on(self, interaction: discord.Interaction):
        config = load_config()
        config["anti_link"]["enabled"] = True
        save_config(config)
        await interaction.response.send_message("✅ Anti-Link is now **Enabled**.")

    @app_commands.command(name="antilink_off", description="Disable anti-link protection")
    async def antilink_off(self, interaction: discord.Interaction):
        config = load_config()
        config["anti_link"]["enabled"] = False
        save_config(config)
        await interaction.response.send_message("❌ Anti-Link is now **Disabled**.")

    @app_commands.command(name="antilink_bypass", description="[PREMIUM] Set bypass roles")
    async def antilink_bypass(self, interaction: discord.Interaction, role: discord.Role):
        if not is_user_premium(interaction.user.id):
            return await interaction.response.send_message("⭐ **Premium Only!**", ephemeral=True)

        config = load_config()
        if "bypass_roles" not in config["anti_link"]:
            config["anti_link"]["bypass_roles"] = []
            
        if role.id in config["anti_link"]["bypass_roles"]:
            config["anti_link"]["bypass_roles"].remove(role.id)
            msg = f"✅ Role {role.name} removed from bypass."
        else:
            config["anti_link"]["bypass_roles"].append(role.id)
            msg = f"✅ Role {role.name} added to bypass."
        
        save_config(config)
        await interaction.response.send_message(msg)

    @app_commands.command(name="antilink_dashboard", description="Show anti-link dashboard")
    async def antilink_dashboard(self, interaction: discord.Interaction):
        config = load_config()
        al = config.get("anti_link", {})
        embed = discord.Embed(title="🚫 Anti-Link Dashboard", color=discord.Color.blue())
        embed.add_field(name="Status", value="🟢 Enabled" if al.get("enabled") else "🔴 Disabled")
        embed.add_field(name="Bypass Roles", value=len(al.get("bypass_roles", [])))
        if "image_url" in al:
            embed.set_image(url=al["image_url"])
        await interaction.response.send_message(embed=embed, view=AntiLinkView())

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
        
