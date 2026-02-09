import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio  # এটি খুবই গুরুত্বপূর্ণ, যা ক্রাশ রোধ করবে

# Railway Token
TOKEN = os.getenv('DISCORD_TOKEN')

# টিকিট কাউন্টার (বট রিস্টার্ট দিলে এটি ০ হবে, ডাটাবেজ ছাড়া এটিই নিয়ম)
ticket_data = {"count": 0}

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Persistent Views: যাতে বট রিস্টার্ট হলেও বাটন কাজ করে
        self.add_view(TicketLauncher())
        self.add_view(TicketControl())
        await self.tree.sync()
        print(f"✅ Unique Ticket System Synced")

bot = MyBot()

# ================= ইউনিক টিকিট সিস্টেম লজিক =================



class TicketControl(View):
    """টিকিট চ্যানেলের ভেতরের কন্ট্রোল বাটন"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_btn")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.send_message("⚠️ এই টিকিটটি ৫ সেকেন্ডের মধ্যে ডিলিট হয়ে যাবে...", ephemeral=False)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="🙋‍♂️", custom_id="claim_btn")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ শুধুমাত্র স্টাফরা এটি ক্লেম করতে পারবেন!", ephemeral=True)
        
        await interaction.response.send_message(f"✅ এই টিকিটটি এখন থেকে {interaction.user.mention} হ্যান্ডেল করছেন।", ephemeral=False)
        self.claim.disabled = True
        await interaction.message.edit(view=self)

class TicketDropdown(Select):
    """ড্রপডাউন মেনু যেখানে ক্যাটাগরি থাকবে"""
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", description="সাধারণ সমস্যার জন্য", emoji="🛠️"),
            discord.SelectOption(label="Report Member", description="কাউকে রিপোর্ট করতে", emoji="🚫"),
            discord.SelectOption(label="Giveaway/Prizes", description="পুরস্কার সংক্রান্ত", emoji="🎁"),
        ]
        super().__init__(placeholder="টিকিট খোলার কারণ নির্বাচন করুন...", min_values=1, max_values=1, options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        # সিরিয়াল নাম্বার বাড়ানো
        ticket_data["count"] += 1
        num = ticket_data["count"]
        
        guild = interaction.guild
        user = interaction.user
        category_name = "🎫 ACTIVE TICKETS"
        
        # ক্যাটাগরি তৈরি বা চেক করা
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        # পারমিশন লজিক: শুধু ওই ইউজার এবং অ্যাডমিনরা দেখবে
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # ইউনিক চ্যানেল নাম: ticket-1, ticket-2
        channel = await guild.create_text_channel(
            name=f"ticket-{num}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(f"✅ আপনার টিকিট তৈরি হয়েছে: {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title=f"Support Ticket #{num}",
            description=f"হ্যালো {user.mention}, আমাদের সাপোর্ট টিমে আপনাকে স্বাগতম।\nদয়া করে আপনার সমস্যার কথা লিখুন। স্টাফরা দ্রুত আপনার সাথে যোগাযোগ করবে।",
            color=discord.Color.from_rgb(88, 101, 242)
        )
        embed.add_field(name="Category", value=self.values[0])
        embed.set_footer(text="Unique Ticket Management")
        
        await channel.send(embed=embed, view=TicketControl())

class TicketLauncher(View):
    """টিকিট শুরুর মেইন ভিউ"""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

# ================= কমান্ডস =================

@bot.tree.command(name="ticket_setup", description="অ্যাডভান্সড টিকিট সিস্টেম সেটআপ করুন")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = discord.Embed(
        title="📩 সাপোর্ট সেন্টার",
        description="আমাদের সাথে সরাসরি কথা বলতে নিচের ড্রপডাউন মেনু থেকে সঠিক ক্যাটাগরি সিলেক্ট করে টিকিট ওপেন করুন।",
        color=discord.Color.blue()
    )
    # একটি ইউনিক লুক দেওয়ার জন্য ব্যানার ইমেজ (অপশনাল)
    embed.set_image(url="https://i.imgur.com/vHq49Yj.png") 
    
    await channel.send(embed=embed, view=TicketLauncher())
    await interaction.response.send_message("✅ টিকিট সিস্টেম সফলভাবে সেটআপ হয়েছে!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'🚀 {bot.user.name} ইউনিক টিকিট সিস্টেম চালু হয়েছে!')

# রেলওয়ে হোস্টিং এর জন্য এরর হ্যান্ডলিং
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ বট চালু হতে সমস্যা হয়েছে: {e}")
