import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Centralized Ticket Data
server_data = {
    "ticket_count": 0,
    "dashboard": {
        "title": "📩 সাপোর্ট সেন্টার",
        "description": "আমাদের সাথে কথা বলতে নিচের মেনু থেকে ক্যাটাগরি সিলেক্ট করুন।",
        "image": "https://i.imgur.com/vHq49Yj.png"
    },
    "inside_message": {
        "title": "সহায়তা টিকিট",
        "description": "হ্যালো {member}, আমাদের সাপোর্ট টিম আপনার জন্য অপেক্ষা করছে। আপনার সমস্যাটি বিস্তারিত লিখুন।",
        "color": discord.Color.blue().value
    }
}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # রিস্টার্টের পরেও যেন বাটন ও ড্রপডাউন কাজ করে
        self.add_view(TicketLauncher())
        self.add_view(TicketControl())
        await self.tree.sync()
        print("✅ সব কমান্ড এবং বাটন সিঙ্ক হয়েছে।")

bot = MyBot()

# ================= MODALS FOR DASHBOARD =================

class DashboardEditModal(Modal, title="এডিট টিকিট ড্যাশবোর্ড"):
    title_in = TextInput(label="টাইটেল", default=server_data["dashboard"]["title"])
    desc_in = TextInput(label="ডেসক্রিপশন", style=discord.TextStyle.paragraph, default=server_data["dashboard"]["description"])
    img_in = TextInput(label="ইমেজ লিঙ্ক (URL)", default=server_data["dashboard"]["image"], required=False)

    async def on_submit(self, interaction: discord.Interaction):
        server_data["dashboard"].update({
            "title": self.title_in.value,
            "description": self.desc_in.value,
            "image": self.img_in.value
        })
        await interaction.response.send_message("✅ ড্যাশবোর্ড আপডেট হয়েছে! এখন `/ticket_setup` দিন।", ephemeral=True)

class InsideEditModal(Modal, title="টিকিটের ভেতরের মেসেজ এডিট"):
    title_in = TextInput(label="টিকিট টাইটেল", default=server_data["inside_message"]["title"])
    desc_in = TextInput(label="টিকিট ডেসক্রিপশন", style=discord.TextStyle.paragraph, default=server_data["inside_message"]["description"])

    async def on_submit(self, interaction: discord.Interaction):
        server_data["inside_message"].update({
            "title": self.title_in.value,
            "description": self.desc_in.value
        })
        await interaction.response.send_message("✅ টিকিটের ভেতরের মেসেজ আপডেট হয়েছে!", ephemeral=True)

# ================= TICKET UI COMPONENTS =================

class TicketControl(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close_permanent")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ টিকিটটি ৫ সেকেন্ডের মধ্যে বন্ধ হয়ে যাবে...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="ticket_claim_permanent")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ শুধুমাত্র স্টাফরা এটি ক্লেম করতে পারবে।", ephemeral=True)
        await interaction.response.send_message(f"✅ টিকিটটি {interaction.user.mention} গ্রহণ করেছেন।", ephemeral=False)
        self.claim.disabled = True
        await interaction.message.edit(view=self)

class TicketDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", description="সাধারণ সমস্যার জন্য", emoji="🛠️"),
            discord.SelectOption(label="Report", description="রিপোর্ট করার জন্য", emoji="🚫")
        ]
        super().__init__(placeholder="বিভাগ সিলেক্ট করুন...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown_permanent")

    async def callback(self, interaction: discord.Interaction):
        server_data["ticket_count"] += 1
        num = server_data["ticket_count"]
        
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="🎫 TICKETS")
        if not category:
            category = await guild.create_category("🎫 TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(name=f"ticket-{num}", category=category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ আপনার টিকিট তৈরি হয়েছে: {channel.mention}", ephemeral=True)

        # টিকিটের ভেতর মেসেজ পাঠানো
        config = server_data["inside_message"]
        embed = discord.Embed(
            title=config["title"], 
            description=config["description"].replace("{member}", interaction.user.mention), 
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=TicketControl())

class TicketLauncher(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ================= COMMANDS =================

@bot.tree.command(name="ticket_setup", description="টিকিট সিস্টেম চালু করুন")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    config = server_data["dashboard"]
    embed = discord.Embed(
        title=config["title"], 
        description=config["description"], 
        color=discord.Color.green()
    )
    if config["image"]:
        embed.set_image(url=config["image"])
    
    # এখানে TicketLauncher() ভিউটি পাঠানো হচ্ছে যাতে ড্রপডাউন কাজ করে
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message(f"✅ টিকিট সিস্টেম {channel.mention} এ সেটআপ হয়েছে।", ephemeral=True)

@bot.tree.command(name="ticket_dashboard", description="টিকিট সেটিংস কন্ট্রোল প্যানেল")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_dashboard(interaction: discord.Interaction):
    view = View()
    btn1 = Button(label="Edit Dashboard", style=discord.ButtonStyle.primary, emoji="📝")
    btn2 = Button(label="Edit Inside Message", style=discord.ButtonStyle.secondary, emoji="💬")
    
    async def cb1(i): await i.response.send_modal(DashboardEditModal())
    async def cb2(i): await i.response.send_modal(InsideEditModal())
    
    btn1.callback = cb1; btn2.callback = cb2
    view.add_item(btn1); view.add_item(btn2)
    
    await interaction.response.send_message("⚙️ **টিকিট কন্ট্রোল ড্যাশবোর্ড**", view=view, ephemeral=True)

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} ইজ অনলাইন!')

bot.run(TOKEN)
bot.run(TOKEN)
