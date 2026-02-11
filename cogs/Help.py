import discord
from discord.ext import commands
from discord import app_commands

# --- ১. ড্রপডাউন মেনু ক্লাস ---
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Economy & Hunting", emoji="💰", description="Money, Zoo, Hunting & Inventory"),
            discord.SelectOption(label="Games & Gambling", emoji="🎲", description="Blackjack, Slots, Coinflip & Lottery"),
            discord.SelectOption(label="Roleplay & Social", emoji="🎭", description="Hug, Kiss, Profile & Interactions"),
            discord.SelectOption(label="Moderation & Security", emoji="🛡️", description="Ban, Kick, Nuke & Security tools"),
            discord.SelectOption(label="Utility & Tools", emoji="🛠️", description="Serverinfo, Avatar, Say & Premium"),
        ]
        super().__init__(placeholder="Select a category for Wow...", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # --- ক্যাটাগরি ১: ইকোনমি ও হান্টিং ---
        if self.values[0] == "Economy & Hunting":
            embed = discord.Embed(title="💰 Wow Economy & Hunting", color=discord.Color.green())
            embed.add_field(name="💸 Money", value="`/bal`, `/daily`, `/give`, `/sell`", inline=False)
            embed.add_field(name="🏹 Hunting", value="`/hunt`, `/use`, `/open`, `/zoo`", inline=False)
            embed.add_field(name="🎒 Items", value="`/inventory`, `/top`", inline=False)
            await interaction.response.edit_message(embed=embed)

        # --- ক্যাটাগরি ২: গেমস ---
        elif self.values[0] == "Games & Gambling":
            embed = discord.Embed(title="🎲 Wow Games & Casino", color=discord.Color.gold())
            embed.add_field(name="🃏 Cards", value="`/blackjack`", inline=True)
            embed.add_field(name="🪙 Coin", value="`/cf` (Coinflip)", inline=True)
            embed.add_field(name="🎰 Luck", value="`/slot`, `/lottery`", inline=True)
            await interaction.response.edit_message(embed=embed)

        # --- ক্যাটাগরি ৩: রোলপ্লে ---
        elif self.values[0] == "Roleplay & Social":
            embed = discord.Embed(title="🎭 Wow Roleplay", color=discord.Color.purple())
            embed.add_field(name="💞 Actions", value="`/bite`, `/fuck`, `/hug`, `/kill`, `/kiss`, `/slap`", inline=False)
            embed.add_field(name="👤 User", value="`/profile`, `/avatar`, `/banner`", inline=False)
            await interaction.response.edit_message(embed=embed)

        # --- ক্যাটাগরি ৪: মডারেশন ---
        elif self.values[0] == "Moderation & Security":
            embed = discord.Embed(title="🛡️ Wow Moderation", color=discord.Color.red())
            embed.add_field(name="🔨 Actions", value="`/ban`, `/unban`, `/clear`", inline=False)
            embed.add_field(name="🔒 Channel", value="`/lock`, `/unlock`, `/nuke`", inline=False)
            embed.add_field(name="📢 Server", value="`/announce`, `/emergency_wipe`", inline=False)
            await interaction.response.edit_message(embed=embed)
            
        # --- ক্যাটাগরি ৫: ইউটিলিটি ---
        elif self.values[0] == "Utility & Tools":
            embed = discord.Embed(title="🛠️ Wow Utilities", color=discord.Color.blue())
            embed.add_field(name="ℹ️ Info", value="`/serverinfo`, `/invites`", inline=True)
            embed.add_field(name="🗣️ Bot Talk", value="`/say`, `/embed`", inline=True)
            embed.add_field(name="💎 Premium", value="`/premium_list`", inline=True)
            await interaction.response.edit_message(embed=embed)

# --- ২. ভিউ ক্লাস ---
class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

# --- ৩. মেইন কমান্ড ---
class CustomHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # hybrid_command এর কারণে এটি !help এবং /help দুটোতেই কাজ করবে
    # aliases=["h", "cmds"] এর কারণে !h বা !cmds দিলেও কাজ করবে
    @commands.hybrid_command(name="help", description="📜 Show all commands for Wow", aliases=["h", "cmds", "commands"])
    async def help(self, ctx):
        embed = discord.Embed(
            title="🌟 Wow Help Menu",
            description="Hello! I am **Wow**. Select a category from the **Dropdown Menu** below to explore my features.",
            color=discord.Color.from_rgb(43, 45, 49)
        )
        # আপনার বটের প্রোফাইল পিকচার সেট করা থাকলে সেটি এখানে দেখাবে
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text=f"Requested by {ctx.author.name} | Wow System")
        
        view = HelpView()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(CustomHelp(bot))
          
