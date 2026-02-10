import discord
from discord.ext import commands
import json
import os
import re

DB_FILE = 'economy.json'

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {}

def save_data(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=4)

# --- বাটন ভিউ ক্লাস ---
class ConfirmView(discord.ui.View):
    def __init__(self, ctx, target, amount, data):
        super().__init__(timeout=30) # ৩০ সেকেন্ড সময় থাকবে
        self.ctx = ctx
        self.target = target
        self.amount = amount
        self.data = data
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ এই বাটনটি আপনার জন্য নয়!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ব্যালেন্স আবার চেক করা (হ্যাক ঠেকানোর জন্য)
        user_id = str(self.ctx.author.id)
        target_id = str(self.target.id)
        
        # ডাটা আবার লোড করা যাতে রিয়েল টাইম ব্যালেন্স পাওয়া যায়
        fresh_data = load_data() 
        
        if fresh_data.get(user_id, {}).get("balance", 0) < self.amount:
            await interaction.response.edit_message(content="❌ ট্রানজেকশন ফেইলড! আপনার পর্যাপ্ত টাকা নেই।", embed=None, view=None)
            return

        # টাকা কাটা এবং যোগ করা
        fresh_data[user_id]["balance"] -= self.amount
        
        if target_id not in fresh_data:
            fresh_data[target_id] = {"balance": 0}
        fresh_data[target_id]["balance"] += self.amount
        
        save_data(fresh_data)
        
        embed = discord.Embed(
            description=f"✅ **Successful!** আপনি **{self.target.mention}** কে **{self.amount:,}** টাকা পাঠিয়েছেন।",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            description="❌ **Cancelled!** ট্রানজেকশন বাতিল করা হয়েছে।",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.value = False
        self.stop()

class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="give", description="Transfer money to another user")
    async def give(self, ctx, *, args: str = None):
        if not args:
            return await ctx.send("❌ ব্যবহার: `Wow give @user 1000` অথবা `Wow give 1000 @user`", ephemeral=True)

        # --- স্মার্ট ইনপুট ডিটেকশন (Regex) ---
        # ১. ইউজার মেনশন খোঁজা (<@12345...>)
        user_match = re.search(r'<@!?(\d+)>', args)
        # ২. টাকার পরিমাণ খোঁজা (10k, 10000, etc.)
        amount_match = re.search(r'(\d+[kK]?)', args.replace(',', '')) 

        if not user_match or not amount_match:
            return await ctx.send("❌ কাকে টাকা পাঠাবেন এবং কত টাকা, তা ঠিকমতো লিখুন।", ephemeral=True)

        target_id = int(user_match.group(1))
        target = ctx.guild.get_member(target_id)
        
        if not target:
            return await ctx.send("❌ মেম্বারকে খুঁজে পাওয়া যাচ্ছে না।", ephemeral=True)

        if target.id == ctx.author.id:
            return await ctx.send("❌ আপনি নিজেকে টাকা পাঠাতে পারবেন না!", ephemeral=True)
            
        if target.bot:
            return await ctx.send("❌ আপনি বটকে টাকা পাঠাতে পারবেন না!", ephemeral=True)

        # টাকার অ্যামাউন্ট প্রসেসিং (k বা K থাকলে হ্যান্ডেল করা)
        raw_amount = amount_match.group(1).lower()
        if 'k' in raw_amount:
            amount = int(float(raw_amount.replace('k', '')) * 1000)
        else:
            amount = int(raw_amount)

        if amount <= 0:
            return await ctx.send("❌ টাকার পরিমাণ অবশ্যই পজিটিভ হতে হবে।", ephemeral=True)

        # --- ব্যালেন্স চেক ---
        data = load_data()
        user_id = str(ctx.author.id)
        
        if user_id not in data:
            data[user_id] = {"balance": 0}
            
        current_balance = data[user_id]["balance"]

        if current_balance < amount:
            return await ctx.send(f"❌ আপনার কাছে পর্যাপ্ত টাকা নেই! আপনার আছে: **{current_balance:,}**", ephemeral=True)

        # --- কনফার্মেশন এমবেড ---
        embed = discord.Embed(
            title="💸 Money Transfer",
            description=f"আপনি কি **{target.mention}** কে **{amount:,}** টাকা পাঠাতে চান?",
            color=0xf1c40f # গোল্ডেন কালার
        )
        embed.set_footer(text="Confirm করার জন্য নিচের বাটনে ক্লিক করুন (30s)")

        view = ConfirmView(ctx, target, amount, data)
        msg = await ctx.send(embed=embed, view=view)

        # টাইমআউট হলে বাটন ডিজেবল করা
        await view.wait()
        if view.value is None:
            embed.description = "⏰ **Time's up!** ট্রানজেকশন বাতিল হয়ে গেছে।"
            embed.color = discord.Color.red()
            await msg.edit(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Give(bot))
      
