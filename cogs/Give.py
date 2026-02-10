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

        # Process Transaction
        data[sender_id]["balance"] -= self.amount
        if receiver_id not in data: data[receiver_id] = {"balance": 0}
        data[receiver_id]["balance"] += self.amount
        save_data(data)

        # UI Change after confirmation (Matches your screenshot)
        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            f"━━━━━━━━━━━━━━━\n"
            f"💰 Transaction Amount: **{self.amount:,} currency!!**\n\n"
            f"⚠️ **Violation Warning:**\n"
            f"Cowoncy never accepts transactions with real money, cryptocurrency, nitro, or anything similar.\n\n"
            f"You have **Confirmed** the transaction. ✅\n"
            f"Confirmed.\n"
            f"━━━━━━━━━━━━━━━"
        )
        embed.set_footer(text=f"{self.ctx.author.name}, you have sent currency to {self.target.name}", icon_url=self.ctx.author.display_avatar.url)
        
        # Header text above embed
        header = f"💳 | @{self.ctx.author.name} **Sent {self.amount:,} currency** to @{self.target.name} (edited)"
        
        await interaction.response.edit_message(content=header, embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Transaction Cancelled.", embed=None, view=None)

class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="give", description="Send currency to another user")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def give(self, ctx, *, args: str = None):
        if not args:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❓ **Usage:** `Wow give @user 1000`", ephemeral=True)

        # --- Improved Detection (Fixed ID issue) ---
        user_match = re.search(r'<@!?(\d+)>', args)
        amount_match = re.search(r'(\d+)', args.replace(',', ''))

        if not user_match or not amount_match:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Could not find a valid user or amount in your message.")

        target_id = int(user_match.group(1))
        target = ctx.guild.get_member(target_id) or await self.bot.fetch_user(target_id)
        amount = int(amount_match.group(1))

        if target.id == ctx.author.id:
            return await ctx.send("❌ You cannot give money to yourself!")

        data = load_data()
        balance = data.get(str(ctx.author.id), {}).get("balance", 0)

        if balance < amount:
            return await ctx.send(f"❌ You don't have enough money! Balance: **{balance:,}**")

        # --- UI Design (Matches your 1st Screenshot) ---
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
