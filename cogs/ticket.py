import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
import asyncio

# কনফিগারেশন
ticket_config = {"gif_url": None}

# ১. ড্রপডাউন মেনু
class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="BUY", emoji="🛒"),
            discord.SelectOption(label="REPORT", emoji="📩"),
            discord.SelectOption(label="CLAIM", emoji="🎁"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown_select")

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
        
        embed = discord.Embed(title=f"Support - {category}", description=f"হ্যালো {user.mention}, আপনার টিকিটটি খোলা হয়েছে।", color=discord.Color.blue())
        if ticket_config["gif_url"]: embed.set_image(url=ticket_config["gif_url"])
            
        # এখানে TicketControl() ভিউটি পাঠানো হচ্ছে যেন ক্লোজ বাটন কাজ করে
        await channel.send(embed=embed, view=TicketControl())
        await interaction.response.send_message(f"✅ টিকিট তৈরি হয়েছে: {channel.mention}", ephemeral=True)

# ২. টিকিটের ভেতরের ক্লোজ বাটন (এটিই আপনার মেইন প্রবলেম ছিল)
class TicketControl(View):
    def __init__(self):
        # timeout=None দেওয়া হয়েছে যেন বাটন কখনো নষ্ট না হয়
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_id")
    async def close(self, interaction: discord.Interaction):
        # রেসপন্স দিতে দেরি হলে interaction failed আসে, তাই প্রথমে defer করা ভালো
        await interaction.response.send_message("⚠️ ৫ সেকেন্ডের মধ্যে টিকিট ডিলিট হচ্ছে...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# ৩. মেইন লঞ্চার
class TicketLaunch(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class TicketSystem(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="setup_ticket", description="টিকিট সিস্টেম সেটআপ করুন")
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📩 Support Ticket", description="নিচের ড্রপডাউন থেকে ক্যাটাগরি বেছে নিন।", color=discord.Color.green())
        await interaction.channel.send(embed=embed, view=TicketLaunch())
        await interaction.response.send_message("✅ সফলভাবে সেটআপ হয়েছে!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
    
