import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import asyncio

# ফাইল পাথ
ECO_FILE = 'economy.json'

def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- কার্ড কনফিগারেশন ---
SUITS = ['♠️', '♥️', '♦️', '♣️']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, amount, deck, player_hand, dealer_hand):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.amount = amount
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.ended = False

    def calculate_score(self, hand):
        score = 0
        aces = 0
        for card in hand:
            rank = card[1]
            score += VALUES[rank]
            if rank == 'A':
                aces += 1
        
        while score > 21 and aces:
            score -= 10
            aces -= 1
        return score

    def format_hand(self, hand, hide_second=False):
        if hide_second:
            return f"`[{hand[0][0]} {hand[0][1]}]` `[? ?]`"
        return " ".join([f"`[{s} {r}]`" for s, r in hand])

    async def end_game(self, interaction, result, color):
        self.ended = True
        
        # বাটন ডিজেবল করা
        for child in self.children:
            child.disabled = True
        
        # ইকোনমি আপডেট
        data = load_json(ECO_FILE)
        uid = str(self.ctx.author.id)
        
        if result == "win":
            winnings = self.amount * 2
            data[uid]["balance"] += winnings
            footer_text = f"You won {winnings:,} coins!"
        elif result == "push":
            data[uid]["balance"] += self.amount
            footer_text = f"Money returned: {self.amount:,}"
        else: # lose
            footer_text = f"You lost {self.amount:,} coins."
        
        save_json(ECO_FILE, data)

        # ফাইনাল এমবেড
        p_score = self.calculate_score(self.player_hand)
        d_score = self.calculate_score(self.dealer_hand)

        embed = discord.Embed(title=f"🃏 Blackjack | {self.ctx.author.display_name}", color=color)
        embed.add_field(name=f"Your Hand ({p_score})", value=self.format_hand(self.player_hand), inline=False)
        embed.add_field(name=f"Dealer Hand ({d_score})", value=self.format_hand(self.dealer_hand), inline=False)
        embed.set_footer(text=footer_text)

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.ctx.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="👊")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)

        # কার্ড নেওয়া
        self.player_hand.append(self.deck.pop())
        score = self.calculate_score(self.player_hand)

        if score > 21: # Bust (হেরে গেছে)
            await self.end_game(interaction, "lose", discord.Color.red())
        else:
            # আপডেট করা এমবেড
            embed = discord.Embed(title=f"🃏 Blackjack | {self.ctx.author.display_name}", color=discord.Color.blue())
            embed.add_field(name=f"Your Hand ({score})", value=self.format_hand(self.player_hand), inline=False)
            embed.add_field(name="Dealer Hand", value=self.format_hand(self.dealer_hand, hide_second=True), inline=False)
            embed.set_footer(text="Choose Hit or Stand")
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)

        # ডিলারের টার্ন
        p_score = self.calculate_score(self.player_hand)
        d_score = self.calculate_score(self.dealer_hand)

        while d_score < 17:
            self.dealer_hand.append(self.deck.pop())
            d_score = self.calculate_score(self.dealer_hand)

        # রেজাল্ট চেক
        if d_score > 21: # ডিলার বাস্ট
            result = "win"
            color = discord.Color.green()
        elif d_score > p_score: # ডিলার বড়
            result = "lose"
            color = discord.Color.red()
        elif d_score < p_score: # প্লেয়ার বড়
            result = "win"
            color = discord.Color.green()
        else: # সমান
            result = "push"
            color = discord.Color.orange()

        await self.end_game(interaction, result, color)

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="blackjack", description="🃏 Play Blackjack to double your money", aliases=["bj", "21"])
    @app_commands.describe(amount="Amount to bet")
    async def blackjack(self, ctx, amount: int):
        if amount < 50:
            return await ctx.send("❌ Minimum bet is **50** coins.", ephemeral=True)

        data = load_json(ECO_FILE)
        uid = str(ctx.author.id)
        bal = data.get(uid, {}).get("balance", 0)

        if bal < amount:
            return await ctx.send(f"❌ You don't have enough money! Balance: {bal:,}", ephemeral=True)

        # টাকা কেটে নেওয়া (হেরে গেলে আর ফেরত পাবে না, জিতলে দ্বিগুণ পাবে)
        data[uid]["balance"] -= amount
        save_json(ECO_FILE, data)

        # ডেক তৈরি করা
        deck = [(s, r) for s in SUITS for r in RANKS]
        random.shuffle(deck)

        # কার্ড ডিল করা
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        # ভিউ তৈরি
        view = BlackjackView(ctx, amount, deck, player_hand, dealer_hand)
        
        # প্রাথমিক স্কোর
        p_score = view.calculate_score(player_hand)
        
        # ব্ল্যাকজ্যাক চেক (শুরুতেই ২১)
        if p_score == 21:
            data[uid]["balance"] += int(amount * 2.5) # ব্ল্যাকজ্যাক বোনাস
            save_json(ECO_FILE, data)
            embed = discord.Embed(title="🃏 BLACKJACK!", description=f"You got a natural 21! You win **{int(amount * 2.5):,}** coins!", color=discord.Color.gold())
            embed.add_field(name=f"Your Hand ({p_score})", value=view.format_hand(player_hand), inline=False)
            return await ctx.send(embed=embed)

        # গেম শুরু
        embed = discord.Embed(title=f"🃏 Blackjack | {ctx.author.display_name}", color=discord.Color.blue())
        embed.add_field(name=f"Your Hand ({p_score})", value=view.format_hand(player_hand), inline=False)
        embed.add_field(name="Dealer Hand", value=view.format_hand(dealer_hand, hide_second=True), inline=False)
        embed.set_footer(text=f"Bet: {amount:,} coins | Hit 👊 or Stand ✋")

        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Blackjack(bot))
                        
