import discord
from discord.ext import commands
import json
import os

DB_FILE = 'economy.json'

def load_json():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
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
            "Legendary": {"list": ["🐉", "🐲", "🦁", "🦅", "豹", "🦈", "🦍", "🦣", "🦦", "🦥"], "price": 25000, "short": "l"}
        }

    # এখানে aliases থেকে 's', 'S' পুরোপুরি সরিয়ে দেওয়া হয়েছে।
    # এখন শুধু !sell বা !sl লিখলে এটি কাজ করবে।
    @commands.hybrid_command(name="sell", aliases=["sl", "Sell", "SL"], description="Sell animals for cash!")
    async def sell(self, ctx, item: str = None, amount: str = "1"):
        if not item:
            return await ctx.send("❓ **Usage:**\n`Wow sl all` - Sell all\n`Wow sl c` - Sell Common\n`Wow sl 🐱 5` - Sell 5 Cats", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_json()
        
        if user_id not in data or "inventory" not in data[user_id]:
            return await ctx.send("❌ Your zoo is empty!", ephemeral=True)

        user_data = data[user_id]
        inventory = user_data["inventory"]
        
        total_earned = 0
        sold_count = 0
        item_lower = item.lower()

        # 1. Sell All
        if item_lower == "all":
            for cat, info in self.categories.items():
                for animal in info["list"]:
                    count = inventory.get(animal, 0)
                    if count > 0:
                        total_earned += count * info["price"]
                        sold_count += count
                        inventory[animal] = 0

        # 2. Sell by Category Short-name (c, u, r, e, l)
        elif any(item_lower == info["short"] for info in self.categories.values()):
            selected_info = next(info for info in self.categories.values() if item_lower == info["short"])
            for animal in selected_info["list"]:
                count = inventory.get(animal, 0)
                if count > 0:
                    total_earned += count * selected_info["price"]
                    sold_count += count
                    inventory[animal] = 0

        # 3. Sell Specific Animal
        else:
            animal_to_sell = item
            if animal_to_sell not in inventory or inventory[animal_to_sell] <= 0:
                return await ctx.send(f"❌ You don't have {animal_to_sell}!", ephemeral=True)

            current_stock = inventory[animal_to_sell]
            num_to_sell = current_stock if amount.lower() == "all" else int(amount)

            if num_to_sell > current_stock:
                return await ctx.send(f"❌ You only have {current_stock}!", ephemeral=True)

            price = 0
            for info in self.categories.values():
                if animal_to_sell in info["list"]:
                    price = info["price"]; break
            
            total_earned = num_to_sell * price
            sold_count = num_to_sell
            inventory[animal_to_sell] -= num_to_sell

        if total_earned > 0:
            user_data["balance"] = user_data.get("balance", 0) + total_earned
            save_json(data)

            embed = discord.Embed(
                title="💰 Sale Success",
                description=f"Sold **{sold_count:,}** animals for **{total_earned:,}** {self.cash_emoji}",
                color=0x2ecc71
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Nothing found to sell!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SellSystem(bot))
