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

class ConfirmGive(discord.ui.View):
    def __init__(self, ctx, target, amount):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.target = target
        self.amount = amount

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ This confirmation is not for you!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        sender_id = str(self.ctx.author.id)
        receiver_id = str(self.target.id)

        if data.get(sender_id, {}).get("balance", 0) < self.amount:
            return await interaction.response.edit_message(content="❌ Transaction failed! Insufficient funds.", embed=None, view=None)

        data[sender_id]["balance"] -= self.amount
        if receiver_id not in data: data[receiver_id] = {"balance": 0}
        data[receiver_id]["balance"] += self.amount
        save_data(data)

        embed = discord.Embed(color=0x2ecc71)
        embed.description = (
            f"━━━━━━━━━━━━━━━\n"
            f"💰 transaction Amount: **{self.amount:,} currency!!**\n\n"
            f"⚠️ Violation Warning:\n"
            f"Cowoncy never accepts transactions with real money, cryptocurrency, nitro, or anything similar.\n\n"
            f"You have Confirmed the transaction. ✅\n"
            f"Confirmed.\n"
            f"━━━━━━━━━━━━━━━"
        )
        embed.set_footer(text=f"{self.ctx.author.name}, you have sent currency to {self.target.name}", icon_url=self.ctx.author.display_avatar.url)
        header = f"💳 | @{self.ctx.author.name} **Sent {self.amount:,} currency** to @{self.target.name} (edited)"
        await interaction.response.edit_message(content=header, embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ক্যানসেল করার পর লাল এমবেড এবং সঠিক টেক্সট (স্ক্রিনশট অনুযায়ী)
        embed = discord.Embed(color=0xe74c3c)
        embed.description = (
            f"━━━━━━━━━━━━━━━\n"
            f"💰 transaction Amount: **{self.amount:,} currency!!**\n\n"
            f"⚠️ Violation Warning:\n"
            f"Cowoncy never accepts transactions with real money, cryptocurrency, nitro, or anything similar.\n\n"
            f"You have canceled your transaction. ✖️\n"
            f"Canceled.\n"
            f"━━━━━━━━━━━━━━━"
        )
        embed.set_footer(text=f"{self.ctx.author.name}, you are about to give currency to {self.target.name}", icon_url=self.ctx.author.display_avatar.url)
        await interaction.response.edit_message(content=None, embed=embed, view=None)

class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="give", description="Send currency to another user")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def give(self, ctx, *, args: str = None):
        if not args:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❓ **Usage:** `Wow give @user 100` or `Wow give 100 @user`", ephemeral=True)

        # --- Flexible Argument Detection ---
        target = None
        amount = None

        # ১. মেনশন বা আইডি খোঁজা (Regex)
        mention_match = re.search(r'(\d{17,19})', args) # আইডি বা মেনশন থেকে নম্বর বের করা
        if mention_match:
            user_id = int(mention_match.group(1))
            try:
                target = ctx.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
            except:
                target = None

        # ২. এমাউন্ট খোঁজা (মেনশনের আইডি বাদে অন্য নম্বরগুলো)
        numbers = re.findall(r'\d+', args.replace(',', ''))
        for num in numbers:
            n = int(num)
            if target and n == target.id:
                continue # এটি ইউজার আইডি, এমাউন্ট নয়
            else:
                amount = n
                break

        # ৩. ভ্যালিডেশন
        if not target or amount is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Please provide a valid User and Amount! (e.g., `Wow give @user 100` or `Wow give 100 @user`)")

        if target.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ You cannot give money to yourself!")

        data = load_data()
        balance = data.get(str(ctx.author.id), {}).get("balance", 0)

        if balance < amount:
            return await ctx.send(f"❌ You don't have enough money! Balance: **{balance:,}**")

        # --- UI Display ---
        header_text = f"💳 | @{ctx.author.name} is sending **{amount:,} currency** to @{target.name}"
        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            f"━━━━━━━━━━━━━━━\n"
            f"💰 **Transaction Amount:** {amount:,} currency\n\n"
            f"⚠️ **Violation Warning:**\n"
            f"Cowoncy never accepts transactions with real money, cryptocurrency, nitro, or anything similar.\n\n"
            f"To confirm the transaction, press ✅ **Confirm**.\n"
            f"To cancel the transaction, press ❌ **Cancel**.\n"
            f"━━━━━━━━━━━━━━━"
        )
        embed.set_footer(text=f"{ctx.author.name}, you are about to give currency to {target.name}", icon_url=ctx.author.display_avatar.url)

        view = ConfirmGive(ctx, target, amount)
        await ctx.send(content=header_text, embed=embed, view=view)

    @give.error
    async def give_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = f"{error.retry_after:.2f}"
            await ctx.send(f"**⏱ | {ctx.author.display_name}**! Slow down and try again in **{retry_after}s**", delete_after=5)

async def setup(bot):
    await bot.add_cog(Give(bot))
    
