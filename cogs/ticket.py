import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput
import asyncio

# --- গ্লোবাল সেটিংস (ড্যাশবোর্ড দিয়ে যা পরিবর্তন করা যাবে) ---
ticket_config = {
    "title": "📩 Need Support?",
    "description": "Please select a category from the menu below to open a ticket.",
    "gif_url": None
}

# ১. টিকিটের ভেতরের কন্ট্রোল প্যানেল (Close & Claim বাটন)
class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim 🙋‍♂️", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn")
    async def claim(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"✅ এই টিকেটটি {interaction.user.mention} দ্বারা Claim করা হয়েছে।")
        self.claim.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ ৫ সেকেন্ডের মধ্যে টিকেটটি ডিলিট হয়ে যাবে...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# ২. ক্যাটাগরি ড্রপডাউন মেনু
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BUY", emoji="🛒", description="Purchase products"),
            discord.SelectOption(label="REPORT", emoji="📩", description="Report an issue"),
            discord.SelectOption(label="CLAIM", emoji="🎁", description="Claim rewards"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options, custom_id="ticket_category_select")

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
        
        embed = discord.Embed(
            title=f"Support - {category}", 
            description=f"হ্যালো {user.mention}, আপনার টিকেটটি খোলা হয়েছে। আমাদের স্টাফ দ্রুত আপনার সাথে যোগাযোগ করবে।", 
            color=discord.Color.blue()
        )
        if ticket_config["gif_url"]: 
            embed.set_image(url=ticket_config["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ টিকেট তৈরি হয়েছে: {channel.mention}", ephemeral=True)

# ৩. মেইন লঞ্চার ভিউ
class TicketLaunch(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ৪. ড্যাশবোর্ড মোডাল (Customization)
class TicketDashboardModal(Modal, title="Ticket System Dashboard"):
    t_in = TextInput(label="Main Title", default=ticket_config["title"])
    d_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default=ticket_config["description"])
    g_in = TextInput(label="GIF/Image URL", placeholder="https://example.com/image.gif", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_config["title"] = self.title_in.value
        ticket_config["description"] = self.desc_in.value
        ticket_config["gif_url"] = self.gif_in.value if self.gif_in.value else None
        await interaction.response.send_message("✅ ড্যাশবোর্ড আপডেট করা হয়েছে! এখন `/setup_ticket` দিন।", ephemeral=True)

# ৫. মূল Cog ক্লাস
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_dashboard", description="টিকেটের টাইটেল, ডেসক্রিপশন এবং GIF সেট করুন")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket", description="টিকেট সিস্টেমটি চালু করুন")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=ticket_config["title"], 
            description=ticket_config["description"], 
            color=discord.Color.green()
        )
        if ticket_config["gif_url"]: 
            embed.set_image(url=ticket_config["gif_url"])
            
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ টিকেট সিস্টেম সফলভাবে পাঠানো হয়েছে!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
            
