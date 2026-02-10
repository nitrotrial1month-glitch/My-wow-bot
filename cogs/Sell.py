import discord
from discord.ext import commands
import json
import os

# --- Database File Path ---
DB_FILE = 'economy.json'

def load_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_json(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class SellSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cash_emoji = "<:Nova:1453460518764548186>"
        
        # Prices and Categories
        self.categories = {
            "Common": {"list": ["🐭", "🐹", "🐰", "🐱", "🐶", "🦊", "🐻", "🐼", "🐨", "🐯"], "price": 100, "short": "c"},
            "Uncommon": {"list": ["🐸", "🐷", "🐮", "🦁", "🐵", "🐒", "🐔", "🐧", "🐦", "🐤"], "price": 500, "short": "u"},
            "Rare": {"list": ["🦄", "🐴", "🐗", "🦒", "🦓", "🐘", "🦏", "🐫", "🐪", "🦌"], "price": 2500, "short": "r"},
            "Epic": {"list": ["🐍", "🦎", "🦖", "🦕", "🐢", "🐊", "🐙", "🦑", "🐬", "🐳"], "price": 8000, "short": "e"},
            "Legendary": {"list": ["🐉", "🐲", "🦁", "🦅", "🐆", "🦈", "🦍", "🦣", "🦦", "🦥"], "price": 25000, "short": "l"}
        }

    # Aliases থেকে 's' সরিয়ে 'sl' যোগ করা হয়েছে
    @commands.hybrid_command(name="sell", aliases=["Sell", "sl", "SL"], description="Sell animals for global cash!")
    async def sell(self, ctx, item: str = None, amount: str = "1"):
        if not item:
            return await ctx.send("❓ **Usage:**\n`!sell all` - Sell all animals\n`!sl c` - Sell all Common\n`!sl 🐱 5` - Sell 5 Cats", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_json()
        
        if user_id not in data:
            return await ctx.send("❌ You don't have any data in the system!", ephemeral=True)

        user_data = data[user_id]
        inventory = user_data.get("inventory", {})
        
        if not inventory:
            return await ctx.send("❌ Your zoo is empty!", ephemeral=True)

        total_earned = 0
        sold_count = 0
        item_lower = item.lower()

        # --- Case 1: Sell All ---
        if item_lower == "all":
            for cat, info in self.categories.items():
                for animal in info["list"]:
                    count = inventory.get(animal, 0)
                    if count > 0:
                        total_earned += count * info["price"]
                        sold_count += count
                        inventory[animal] = 0

        # --- Case 2: Sell by Category Short-name (c, u, r, e, l) ---
        elif any(item_lower == info["short"] for info in self.categories.values()):
            for cat, info in self.categories.items():
                if item_lower == info["short"]:
                    for animal in info["list"]:
                        count = inventory.get(animal, 0)
                        if count > 0:
                            total_earned += count * info["price"]
                            sold_count += count
                            inventory[animal] = 0

        # --- Case 3: Sell Specific Animal (Emoji) ---
        else:
            animal_to_sell = item
            if animal_to_sell not in inventory or inventory[animal_to_sell] <= 0:
                return await ctx.send(f"❌ You don't have any {animal_to_sell}!", ephemeral=True)

            current_stock = inventory[animal_to_sell]
            
            if amount.lower() == "all":
                num_to_sell = current_stock
            else:
                try:
                    num_to_sell = int(amount)
                except ValueError:
                    return await ctx.send("❌ Amount must be a number or 'all'!", ephemeral=True)

            if num_to_sell > current_stock:
                return await ctx.send(f"❌ You only have {current_stock} of {animal_to_sell}!", ephemeral=True)

            price = 0
            for info in self.categories.values():
                if animal_to_sell in info["list"]:
                    price = info["price"]
                    break
            
            total_earned = num_to_sell * price
            sold_count = num_to_sell
            inventory[animal_to_sell] -= num_to_sell

        if total_earned > 0:
            user_data["balance"] = user_data.get("balance", 0) + total_earned
            user_data["inventory"] = inventory
            save_json(data)

            embed = discord.Embed(
                title="💰 Transaction Successful",
                description=f"Sold **{sold_count:,}** animals for **{total_earned:,}** {self.cash_emoji}",
                color=0x2ecc71
            )
            embed.set_footer(text=f"New Balance: {user_data['balance']:,}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ No matching animals found!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SellSystem(bot))
    
