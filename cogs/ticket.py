import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View
import asyncio

# --- টিকিট সেটিংস স্টোরেজ ---
ticket_settings = {
    "title": "📩 Need Support?",
    "description": "Click the button below to create a private support ticket!",
    "gif_url": None
}

# --- টিকিটের ভেতরের কন্ট্রোল বাটন (Close & Claim) ---
class TicketControl(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim 🙋‍♂️", style=discord.ButtonStyle.success, custom_id="claim_ticket")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ আপনার এই টিকিটটি Claim করার পারমিশন নেই!", ephemeral=True)
        
        await interaction.response.send_message(f"✅ এই টিকিটটি {interaction.user.mention} দ্বারা Claim করা হয়েছে।")
        self.claim.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Close 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ এই টিকিটটি ৫ সেকেন্ডের মধ্যে ডিলিট হয়ে যাবে...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- মেইন টিকিট লঞ্চ বাটন ---
class TicketLaunch(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket 📩", style=discord.ButtonStyle.primary, custom_id="launch_ticket")
    async def create(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        
        # টিকিট চ্যানেলের পারমিশন
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title="Support System",
            description=f"হ্যালো {user.mention}, আমাদের স্টাফ মেম্বাররা আপনার সাথে খুব শীঘ্রই যোগাযোগ করবেন।\nটিকিট ম্যানেজ করতে নিচের বাটনগুলো ব্যবহার করুন।",
            color=discord.Color.blue()
        )
        
        if ticket_settings["gif_url"]:
            embed.set_image(url=ticket_settings["gif_url"])
            
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ টিকিট তৈরি হয়েছে: {channel.mention}", ephemeral=True)

# --- কাস্টমাইজেশন ড্যাশবোর্ড মোডাল ---
class TicketDashboardModal(Modal, title="Ticket Customization"):
    t_in = TextInput(label="Ticket Title", default=ticket_settings["title"])
    d_in = TextInput(label="Description", style=discord.TextStyle.paragraph, default=ticket_settings["description"])
    g_in = TextInput(label="GIF URL (Direct Link)", placeholder="https://example.com/image.gif", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_settings["title"] = self.t_in.value
        ticket_settings["description"] = self.d_in.value
        ticket_settings["gif_url"] = self.g_in.value if self.g_in.value else None
        await interaction.response.send_message("✅ টিকিটের সেটিংস আপডেট করা হয়েছে!", ephemeral=True)

# --- মূল টিকিট Cog ক্লাস ---
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_dashboard", description="টিকিটের মেসেজ এবং GIF কাস্টমাইজ করুন")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketDashboardModal())

    @app_commands.command(name="setup_ticket", description="টিকিট সিস্টেম সেটআপ করুন")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=ticket_settings["title"],
            description=ticket_settings["description"],
            color=discord.Color.green()
        )
        if ticket_settings["gif_url"]:
            embed.set_image(url=ticket_settings["gif_url"])
            
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ টিকিট সিস্টেম পাঠানো হয়েছে!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
