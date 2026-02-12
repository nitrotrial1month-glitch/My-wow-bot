import discord
from discord import app_commands
from discord.ext import commands
import datetime
# utils থেকে প্রিমিয়াম লজিক এবং কনফিগ ইমপোর্ট
from utils import load_config, get_theme_color

# --- ১. প্রিমিয়াম ড্যাশবোর্ড ভিউ (বাটন) ---
class PollControlView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    # 🛑 End Poll Button
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

        # রেজাল্ট এমবেড (Falcon Style)
        embed.color = discord.Color.red()
        embed.title = f"🛑 POLL ENDED"
        embed.description = (
            f"### {embed.title}\n"
            f"────────────────────\n"
            f"**Final Results:**\n{results}\n"
            f"🏆 **Winner:** {winner}\n"
            f"────────────────────"
        )
        embed.set_footer(text="This poll is now closed.")

        await interaction.response.edit_message(embed=embed, view=None)

    # 📊 Live Stats (Ephemeral)
    @discord.ui.button(label="Live Stats", style=discord.ButtonStyle.secondary, emoji="📊")
    async def live_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        reactions = interaction.message.reactions
        stats = "### 📊 Current Poll Stats\n────────────────────\n"
        for reaction in reactions:
            stats += f"{reaction.emoji} : **{reaction.count - 1} votes**\n"
            
        await interaction.response.send_message(stats, ephemeral=True)

# --- ২. মেইন পোল ক্লাস ---
class PollSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    # হেল্পার: প্রিমিয়াম চেক (শুধুমাত্র সার্ভার প্রিমিয়াম)
    def is_premium(self, guild_id):
        color = get_theme_color(guild_id)
        return color == discord.Color.gold()

    @app_commands.command(name="poll", description="📊 Create a stylish poll (10 Options for Premium)")
    @app_commands.describe(
        question="What is your question?",
        options="Comma separated (e.g. Option1, Option2)",
        banner_url="[PREMIUM] Add a big banner/image"
    )
    async def poll(self, interaction: discord.Interaction, question: str, options: str, banner_url: str = None):
        
        is_prem = self.is_premium(interaction.guild.id)
        color = get_theme_color(interaction.guild.id)
        
        # ১. অপশন প্রসেসিং ও লিমিট চেক
        opts_list = [o.strip() for o in options.split(',')]
        count = len(opts_list)
        limit = 10 if is_prem else 5 # প্রিমিয়াম ১০, ফ্রি ৫
        
        if count > limit:
            return await interaction.response.send_message(
                f"⚠️ **Limit Reached!**\nFree Servers: 5 Options\nPremium Servers: 10 Options\n\n⭐ *Upgrade to Premium for more!*", 
                ephemeral=True
            )
        
        if count < 2:
            return await interaction.response.send_message("⚠️ কমপক্ষে ২টি অপশন দিতে হবে!", ephemeral=True)

        # ২. এমবেড ডিজাইন (Nova/Falcon Style)
        description = f"### 📊 {question}\n────────────────────\n"
        for i in range(count):
            description += f"{self.emojis[i]} **{opts_list[i]}**\n\n"
        
        description += "────────────────────\n"
        description += f"• React with the emojis to vote!\n• Hosted by: {interaction.user.mention}"

        embed = discord.Embed(description=description, color=color)
        
        # প্রিমিয়াম হলে ব্যানার ও গোল্ডেন ফুটার
        if is_prem:
            if banner_url: embed.set_image(url=banner_url)
            embed.set_footer(text="💎 Premium Server Poll", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        else:
            embed.set_footer(text="Free Server Poll | Upgrade to /buy_premium")

        # ৩. প্রিমিয়াম ড্যাশবোর্ড বাটন
        view = PollControlView(interaction.user.id) if is_prem else None

        # ৪. মেসেজ পাঠানো
        await interaction.response.send_message("✅ পোল তৈরি করা হচ্ছে...", ephemeral=True)
        msg = await interaction.channel.send(content="📊 **NEW POLL**", embed=embed, view=view)

        # ৫. রিঅ্যাকশন যোগ করা
        for i in range(count):
            await msg.add_reaction(self.emojis[i])

async def setup(bot):
    await bot.add_cog(PollSystem(bot))
