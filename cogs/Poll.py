import discord
from discord import app_commands
from discord.ext import commands
from utils import check_advanced_premium # আপনার utils থেকে ইমপোর্ট

# --- ১. প্রিমিয়াম ড্যাশবোর্ড ভিউ (বাটন) ---
class PollControlView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None) # পোল যতক্ষণ থাকবে, বাটন কাজ করবে
        self.author_id = author_id

    # 🔴 End Poll Button
    @discord.ui.button(label="End Poll", style=discord.ButtonStyle.danger, emoji="🛑")
    async def end_poll(self, interaction: discord.Interaction, button: discord.ui.Button):
        # শুধুমাত্র পোল যে বানিয়েছে সে-ই শেষ করতে পারবে
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ You are not the poll host!", ephemeral=True)

        # রেজাল্ট গণনা
        message = interaction.message
        embed = message.embeds[0]
        reactions = message.reactions
        
        results = ""
        winner = None
        max_votes = -1

        for reaction in reactions:
            count = reaction.count - 1 # বটের নিজের ভোট বাদ দেওয়া হলো
            results += f"{reaction.emoji}: **{count}** votes\n"
            
            if count > max_votes:
                max_votes = count
                winner = reaction.emoji

        # এমবেড আপডেট করা
        embed.color = discord.Color.red()
        embed.title = f"🛑 POLL ENDED: {embed.title}"
        embed.description = f"**Final Results:**\n{results}\n🏆 **Winner:** {winner}"
        embed.set_footer(text="This poll is closed.")

        # বাটন সরিয়ে দেওয়া
        await interaction.response.edit_message(embed=embed, view=None)

    # 📊 Result Button (Privacy Mode)
    @discord.ui.button(label="Live Stats", style=discord.ButtonStyle.primary, emoji="📊")
    async def live_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        # এটি সবাই দেখতে পারবে (Ephemeral)
        message = interaction.message
        reactions = message.reactions
        stats = "**Current Status:**\n"
        
        for reaction in reactions:
            stats += f"{reaction.emoji} : {reaction.count - 1} votes\n"
            
        await interaction.response.send_message(stats, ephemeral=True)

# --- ২. মেইন পোল ক্লাস ---
class PollSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    # হেল্পার: প্রিমিয়াম চেক
    def is_premium(self, user_id, guild_id):
        user_p = check_advanced_premium(user_id)
        server_p = check_advanced_premium(None, guild_id)
        return user_p["active"] or server_p["active"]

    @app_commands.command(name="poll", description="📊 Create a poll (Advanced features for Premium)")
    @app_commands.describe(
        question="What to ask?",
        options="Comma separated options (e.g. Red, Blue, Green)",
        image_url="[PREMIUM] Add an image",
        mention_role="[PREMIUM] Ping a role (e.g. @everyone)"
    )
    async def poll(self, interaction: discord.Interaction, question: str, options: str, image_url: str = None, mention_role: discord.Role = None):
        
        # ১. প্রিমিয়াম স্ট্যাটাস চেক
        premium_user = self.is_premium(interaction.user.id, interaction.guild.id)
        
        # ২. অপশন প্রসেসিং
        opts_list = [o.strip() for o in options.split(',')]
        count = len(opts_list)

        # ৩. লিমিট চেক
        limit = 10 if premium_user else 4 # ফ্রি ইউজার ৪টা, প্রিমিয়াম ১০টা
        
        if count > limit:
            return await interaction.response.send_message(
                f"⚠️ **Limit Reached!**\nFree Limit: 4 Options\nPremium Limit: 10 Options\nYou provided: {count}\n\n⭐ *Upgrade to Premium to add more options!*", 
                ephemeral=True
            )
        
        if count < 2:
            return await interaction.response.send_message("⚠️ You need at least 2 options!", ephemeral=True)

        # ৪. এমবেড তৈরি
        description = ""
        for i in range(count):
            description += f"{self.emojis[i]} **{opts_list[i]}**\n\n"

        embed = discord.Embed(title=question, description=description, color=discord.Color.blue())
        embed.set_footer(text=f"Host: {interaction.user.name} | {'💎 Premium Poll' if premium_user else 'Free Poll'}")

        # ৫. প্রিমিয়াম ফিচার: ইমেজ
        if image_url:
            if premium_user:
                embed.set_image(url=image_url)
            else:
                return await interaction.response.send_message("🔒 **Locked!** Adding images is a Premium feature.", ephemeral=True)

        # ৬. প্রিমিয়াম ফিচার: ড্যাশবোর্ড বাটন
        view = PollControlView(interaction.user.id) if premium_user else None

        # ৭. মেসেজ পাঠানো
        await interaction.response.send_message("✅ Poll created!", ephemeral=True)
        
        # যদি রোল মেনশন থাকে (প্রিমিয়াম ফিচার)
        content = None
        if mention_role:
            if premium_user:
                content = mention_role.mention
            else:
                await interaction.followup.send("🔒 Role ping is a Premium feature (ignored).", ephemeral=True)

        msg = await interaction.channel.send(content=content, embed=embed, view=view)

        # ৮. রিঅ্যাকশন যোগ করা
        for i in range(count):
            await msg.add_reaction(self.emojis[i])

async def setup(bot):
    await bot.add_cog(PollSystem(bot))
          
