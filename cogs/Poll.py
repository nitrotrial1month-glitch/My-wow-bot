import discord
from discord import app_commands
from discord.ext import commands
from utils import load_config, save_config, get_theme_color

# --- ১. পোল ড্যাশবোর্ড মডাল (Full Customization) ---
class PollDashboardModal(discord.ui.Modal, title="💎 Premium Poll Dashboard"):
    def __init__(self):
        super().__init__()
        config = load_config()
        p = config.get("poll_settings", {})
        
        self.title_in = discord.ui.TextInput(label="Poll Title", default=p.get("title"), required=True)
        self.emoji_in = discord.ui.TextInput(label="Poll Emoji", default=p.get("emoji"), required=True)
        self.image_in = discord.ui.TextInput(label="Banner/GIF URL", default=p.get("image_url", ""), required=False)
        self.color_in = discord.ui.TextInput(label="Embed Color (Hex: e.g. #ffcc00)", default="#ffcc00", required=False)
        
        self.add_item(self.title_in)
        self.add_item(self.emoji_in)
        self.add_item(self.image_in)
        self.add_item(self.color_in)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        # হেক্স কালারকে ইন্টিজারে রূপান্তর
        hex_c = self.color_in.value.replace("#", "")
        color_int = int(hex_c, 16) if hex_c else 0xffcc00

        config["poll_settings"] = {
            "title": self.title_in.value,
            "emoji": self.emoji_in.value,
            "image_url": self.image_in.value,
            "color": color_int
        }
        save_config(config)
        await interaction.response.send_message("✅ **Poll Dashboard Settings Updated!**", ephemeral=True)

# --- ২. পোল কন্ট্রোল ভিউ ---
class PollControlView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="End Poll", style=discord.ButtonStyle.danger, emoji="🛑")
    async def end_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ আপনি এই পোলের হোস্ট নন!", ephemeral=True)

        reactions = interaction.message.reactions
        results = ""
        winner = None
        max_votes = -1

        for r in reactions:
            count = r.count - 1
            results += f"{r.emoji} : **{count} votes**\n"
            if count > max_votes:
                max_votes = count
                winner = r.emoji

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.description = f"### 🛑 POLL ENDED\n────────────────────\n**Final Results:**\n{results}\n🏆 **Winner:** {winner}\n────────────────────"
        await interaction.response.edit_message(embed=embed, view=None)

# --- ৩. মেইন পোল ক্লাস ---
class PollSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def is_premium(self, guild_id):
        return get_theme_color(guild_id) == discord.Color.gold()

    @app_commands.command(name="poll_dashboard", description="💎 [PREMIUM] Customize GIF, Emoji & Title")
    @app_commands.checks.has_permissions(administrator=True)
    async def poll_dashboard(self, interaction: discord.Interaction):
        if not self.is_premium(interaction.guild.id):
            return await interaction.response.send_message("💎 এটি শুধুমাত্র **Premium Server**-এর জন্য!", ephemeral=True)
        await interaction.response.send_modal(PollDashboardModal())

    @app_commands.command(name="poll", description="📊 Create a poll (10 options for Premium)")
    @app_commands.describe(question="The question", options="Options separated by comma")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        is_prem = self.is_premium(interaction.guild.id)
        config = load_config()
        p_set = config.get("poll_settings", {})
        
        # অপশন লিমিট চেক
        opts_list = [o.strip() for o in options.split(',')]
        count = len(opts_list)
        limit = 10 if is_prem else 5
        
        if count > limit or count < 2:
            return await interaction.response.send_message(f"⚠️ ২ থেকে {limit} টি অপশন দিন!", ephemeral=True)

        # ডিজাইন (Falcon/Nova Style)
        title = p_set.get("title", "📊 NEW POLL")
        emoji = p_set.get("emoji", "🗳️")
        color = p_set.get("color", 0x3498db) if is_prem else discord.Color.blue().value

        description = f"### {emoji} {title}\n**{question}**\n────────────────────\n"
        for i in range(count):
            description += f"{self.emojis[i]} **{opts_list[i]}**\n\n"
        
        description += f"────────────────────\n• React to vote!\n• Host: {interaction.user.mention}"

        embed = discord.Embed(description=description, color=color)
        
        # প্রিমিয়াম ইমেজ/জিআইএফ এড করা
        if is_prem and p_set.get("image_url"):
            embed.set_image(url=p_set["image_url"])

        view = PollControlView(interaction.user.id) if is_prem else None

        await interaction.response.send_message("✅ পোল তৈরি হচ্ছে...", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=view)

        for i in range(count):
            await msg.add_reaction(self.emojis[i])

async def setup(bot):
    await bot.add_cog(PollSystem(bot))
        
