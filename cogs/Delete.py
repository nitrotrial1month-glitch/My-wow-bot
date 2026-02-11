import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils import check_advanced_premium

class ServerWipeConfirm(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(label="YES, WIPE EVERYTHING", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ This is not for you!", ephemeral=True)

        guild = interaction.guild
        
        # ডিলিট করার আগে ইউজারকে একটি শেষ মেসেজ দেওয়া
        await interaction.response.send_message("🚀 Initiating Server Wipe... Please wait.", ephemeral=True)

        # ১. সব চ্যানেল ডিলিট করা
        for channel in guild.channels:
            try:
                await channel.delete(reason="Emergency Server Reset (Ultra Premium)")
            except:
                continue # কিছু চ্যানেল (যেমন বটের নিজের চ্যানেল) ডিলিট হতে দেরি হতে পারে

        # ২. ডিসকর্ড সার্ভারে অন্তত ১টি চ্যানেল থাকা বাধ্যতামূলক, তাই একটি নতুন চ্যানেল তৈরি করা
        new_channel = await guild.create_text_channel(name="server-reset")
        
        embed = discord.Embed(
            title="🛑 Server Nuked & Secured",
            description="All previous channels have been successfully removed for security purposes.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Emergency Wipe - Ultra Server Premium")
        await new_channel.send(embed=embed)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Not your button!", ephemeral=True)
            
        await interaction.response.edit_message(content="✅ Emergency wipe cancelled.", embed=None, view=None)
        self.stop()

class ServerSecurity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="emergency_wipe", description="🚨 [ULTRA SERVER ONLY] Delete ALL channels in this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def emergency_wipe(self, ctx):
        # ১. ওনার বা এডমিন চেক (এডমিন পারমিশন ডেকোরেটরেই আছে, ওনার চেক আলাদা করা হলো)
        if not ctx.author.guild_permissions.administrator and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Only the **Server Owner** or **Administrators** can use this emergency tool.", ephemeral=True)

        # ২. সার্ভার প্রিমিয়াম চেক (ইউজার প্রিমিয়াম ইগনোর করা হচ্ছে)
        server_status = check_advanced_premium(None, ctx.guild.id)
        
        if not server_status["active"] or server_status["tier"] != "ultra":
            embed = discord.Embed(
                title="🔒 Feature Locked",
                description="This emergency tool requires **Ultra Server Premium**.\nUser Premium is not valid for this command.",
                color=discord.Color.red()
            )
            embed.add_field(name="Required", value="🥇 Ultra Server Tier", inline=True)
            return await ctx.send(embed=embed, ephemeral=True)

        # ৩. কনফার্মেশন প্রম্পট
        confirm_embed = discord.Embed(
            title="🚨 EXTREME DANGER! 🚨",
            description=(
                "You are about to **DELETE EVERY SINGLE CHANNEL** in this server.\n"
                "This action is **PERMANENT** and cannot be undone.\n\n"
                "Do you really want to continue?"
            ),
            color=discord.Color.dark_red()
        )
        confirm_embed.set_footer(text="Requires Administrator & Ultra Server Premium")
        
        view = ServerWipeConfirm(ctx.author.id)
        await ctx.send(embed=confirm_embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerSecurity(bot))
      
