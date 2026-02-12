import discord
from discord import app_commands
from discord.ext import commands
import datetime
from utils import load_config, save_config, get_theme_color

# --- ১. পোল ড্যাশবোর্ড মডাল (Settings Edit) ---
class PollDashboardModal(discord.ui.Modal, title="💎 Premium Poll Dashboard"):
    def __init__(self):
        super().__init__()
        config = load_config()
        poll_data = config.get("poll_settings", {"title": "📊 COMMUNITY POLL"})
        
        self.title_in = discord.ui.TextInput(
            label="Default Poll Title", 
            default=poll_data.get("title", "📊 COMMUNITY POLL"),
            required=True
        )
        self.add_item(self.title_in)

    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        config["poll_settings"] = {"title": self.title_in.value}
        save_config(config)
        await interaction.response.send_message("✅ **Poll Dashboard Settings Updated!**", ephemeral=True)

# --- ২. পোল কন্ট্রোল ভিউ (পোল মেসেজের নিচের বাটন) ---
class PollControlView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="End Poll", style=discord.ButtonStyle.danger, emoji="🛑")
    async def end_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ আপনি এই পোলের হোস্ট নন!", ephemeral=True)

        message = interaction.message
        embed = message.embeds[0]
        reactions = message.reactions
        
        results = ""
        winner = None
        max_votes = -1

        for reaction in reactions:
            count = reaction.count - 1
            results += f"{reaction.emoji} : **{count} votes**\n"
            if count > max_votes:
                max_votes = count
                winner = reaction.emoji

        embed.color = discord.Color.red()
        embed.description = (
            f"### 🛑 POLL ENDED\n"
            f"────────────────────\n"
            f"**Final Results:**\n{results}\n"
            f"🏆 **Winner:** {winner}\n"
            f"────────────────────"
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Stats", style=discord.ButtonStyle.secondary, emoji="📊")
    async def live_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        reactions = interaction.message.reactions
        stats = "### 📊 Current Stats\n"
        for reaction in reactions:
            stats += f"{reaction.emoji} : **{reaction.count - 1} votes**\n"
        await interaction.response.send_message(stats, ephemeral=True)

# --- ৩. মেইন পোল ক্লাস ---
class PollSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def is_premium(self, guild_id):
        return get_theme_color(guild_id) == discord.Color.gold()

    # 💎 আলাদা ড্যাশবোর্ড কমান্ড
    @app_commands.command(name="poll_dashboard", description="💎 [PREMIUM] Configure global poll settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def poll_dashboard(self, interaction: discord.Interaction):
        if not self.is_premium(interaction.guild.id):
            return await interaction.response.send_message("💎 এটি শুধুমাত্র **Premium Server**-এর জন্য!", ephemeral=True)
        await interaction.response.send_modal(PollDashboardModal())

    # 📊 পোল তৈরি কমান্ড
    @app_commands.command(name="poll", description="📊 Create a poll (Up to 10 options for Premium)")
    @app_commands.describe(question="What to ask?", options="Options (comma separated)")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        is_prem = self.is_premium(interaction.guild.id)
        color = get_theme_color(interaction.guild.id)
        
        opts_list = [o.strip() for o in options.split(',')]
        count = len(opts_list)
        limit = 10 if is_prem else 5
        
        if count > limit or count < 2:
            return await interaction.response.send_message(f"⚠️ ২ থেকে {limit} টি অপশন দিন!", ephemeral=True)

        # সেটিংস লোড
        config = load_config()
        default_title = config.get("poll_settings", {}).get("title", "📊 NEW POLL")

        description = f"### {default_title}\n**{question}**\n────────────────────\n"
        for i in range(count):
            description += f"{self.emojis[i]} **{opts_list[i]}**\n\n"
        
        description += f"────────────────────\n• React to vote!\n• Host: {interaction.user.mention}"

        embed = discord.Embed(description=description, color=color)
        view = PollControlView(interaction.user.id) if is_prem else None

        await interaction.response.send_message("✅ পোল তৈরি হচ্ছে...", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=view)

        for i in range(count):
            await msg.add_reaction(self.emojis[i])

async def setup(bot):
    await bot.add_cog(PollSystem(bot))
    
