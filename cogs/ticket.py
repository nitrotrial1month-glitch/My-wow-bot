import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
import asyncio

# --- সেটিংস স্টোরেজ ---
ticket_config = {
    "title": "📩 Need Support?",
    "description": "Please select a category from the menu below.",
    "gif_url": None
}

# ১. টিকেটের ভেতরের বাটন (Close & Claim) - এখানে ভুল ছিল যা ঠিক করা হয়েছে
class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim 🙋‍♂️", style=discord.ButtonStyle.success, custom_id="claim_btn_fixed")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        # button প্যারামিটারটি যোগ করা হয়েছে
        await interaction.response.send_message(f"✅ টিকেটটি {interaction.user.mention} দ্বারা Claim করা হয়েছে।")
        button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_btn_fixed")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # button প্যারামিটারটি যোগ করা হয়েছে
        await interaction.response.send_message("⚠️ ৫ সেকেন্ডের মধ্যে টিকেটটি ডিলিট হয়ে যাবে...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# ২. ক্যাটাগরি ড্রপডাউন
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BUY", emoji="🛒"),
            discord.SelectOption(label="REPORT", emoji="📩"),
            discord.SelectOption(label="CLAIM", emoji="🎁"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options, custom_id="dropdown_fixed")

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        guild = interaction.guild
        user = interaction.user
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"{category.lower()}-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(title=f"Support - {category}", description=f"হ্যালো {user.mention}, আপনার টিকেটটি খোলা হয়েছে।", color=discord.Color.blue())
        if ticket_config["gif_url"]: embed.set_image(url=ticket_config["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ টিকেট তৈরি হয়েছে: {channel.mention}", ephemeral=True)

# ৩. মেইন লঞ্চার
class TicketLaunch(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ৪. ড্যাশবোর্ড মোডাল
class TicketDashboardModal(Modal, title="Customize Ticket"):
    t_in = TextInput(label="Title", default=ticket_config["title"])
    d_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default=ticket_config["description"])
    g_in = TextInput(label="GIF URL", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_config["title"], ticket_config["description"] = self.t_in.value, self.d_in.value
        ticket_config["gif_url"] = self.g_in.value if self.g_in.value else None
        await interaction.response.send_message("✅ ড্যাশবোর্ড আপডেট হয়েছে!", ephemeral=True)

class TicketSystem(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="ticket_dashboard")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(title=ticket_config["title"], description=ticket_config["description"], color=discord.Color.green())
        if ticket_config["gif_url"]: embed.set_image(url=ticket_config["gif_url"])
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ টিকেট সিস্টেম পাঠানো হয়েছে!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
    
