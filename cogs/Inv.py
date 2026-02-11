    @commands.hybrid_command(name="inventory", aliases=["inv", "i"], description="Check your animals and gems")
    async def inventory(self, ctx):
        data = load_json()
        user_id = str(ctx.author.id)

        if user_id not in data or (not data[user_id].get("inventory") and not data[user_id].get("gems")):
            return await ctx.send(f"🎒 | **{ctx.author.display_name}**, your inventory is empty! Go hunt some animals.")

        user_data = data[user_id]
        inventory = user_data.get("inventory", {})
        gems = user_data.get("gems", {})
        
        # --- ১. এনিমেল সেকশন সাজানো ---
        animal_list = []
        if inventory:
            # সংখ্যা অনুযায়ী বড় থেকে ছোট হিসেবে সাজানো
            sorted_animals = sorted(inventory.items(), key=lambda x: x[1], reverse=True)
            for emoji, count in sorted_animals:
                if count > 0:
                    animal_list.append(f"{emoji} `x{count}`")
        
        animals_str = ", ".join(animal_list) if animal_list else "No animals caught yet."

        # --- ২. জেমস সেকশন সাজানো ---
        gem_list = []
        if gems:
            for code, count in gems.items():
                if count > 0:
                    gem_name = self.gems[code]["name"]
                    gem_list.append(f"● `{code}` **{gem_name}** (Stock: {count})")
        
        gems_str = "\n".join(gem_list) if gem_list else "No gems in stock."

        # --- ৩. একটিভ বাফ সেকশন ---
        active_buff = user_data.get("active_buff")
        if active_buff:
            buff_status = f"✅ `{active_buff}` **{self.gems[active_buff]['name']}**\n🔋 Uses left: `{user_data['gem_uses']}`"
        else:
            buff_status = "❌ No active gem"

        # --- ৪. এমবেড ডিজাইন ---
        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s Global Inventory",
            color=0x3498db
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        embed.add_field(name="✨ Active Buff", value=buff_status, inline=False)
        embed.add_field(name="📦 Gems Collection", value=gems_str, inline=False)
        embed.add_field(name="🐾 Animals Caught", value=animals_str[:1024], inline=False) # Discord Limit Check

        embed.set_footer(text=f"Balance: {user_data.get('balance', 0)} | Lootboxes: {user_data.get('lootboxes', 0)}")
        
        await ctx.send(embed=embed)
      
