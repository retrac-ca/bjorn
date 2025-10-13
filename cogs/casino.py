"""
Casino Commands - Gambling games
"""
import random
from typing import Optional


import discord
from discord import app_commands
from discord.ext import commands


from utils.logger import get_logger



class CasinoCog(commands.Cog, name="Casino"):
    """Casino and gambling commands"""


    def __init__(self, bot):
        self.bot = bot
        self.logger = get_logger(__name__)


    async def _check_bet(self, interaction: discord.Interaction, amount: int) -> Optional[bool]:
        """Validate bet amount and user balance"""
        if amount <= 0:
            await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
            return False


        user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)
        if user.balance < amount:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You have ${user.balance:,}",
                ephemeral=True
            )
            return False


        return True


    @app_commands.command(name="coinflip", description="Flip a coin - double or nothing!")
    @app_commands.describe(
        bet="Amount to bet",
        choice="Your prediction: heads or tails"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: str):
        """50/50 coinflip game"""
        if not await self._check_bet(interaction, bet):
            return


        # Flip the coin
        result = random.choice(["heads", "tails"])
        won = result == choice


        if won:
            winnings = bet
            await self.bot.db.update_user_balance(interaction.user.id, winnings)
            
            embed = discord.Embed(
                title="🪙 Coinflip - YOU WIN!",
                description=f"The coin landed on **{result.upper()}**!\n\nYou won **${winnings:,}**!",
                color=discord.Color.green()
            )
        else:
            await self.bot.db.update_user_balance(interaction.user.id, -bet)
            
            embed = discord.Embed(
                title="🪙 Coinflip - You Lost",
                description=f"The coin landed on **{result.upper()}**!\n\nYou lost **${bet:,}**",
                color=discord.Color.red()
            )


        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'coinflip_win' if won else 'coinflip_loss',
            winnings if won else -bet,
            f'Coinflip: {choice} vs {result}'
        )


        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="slots", description="Play the slot machine!")
    @app_commands.describe(bet="Amount to bet")
    async def slots(self, interaction: discord.Interaction, bet: int):
        """Slot machine game"""
        if not await self._check_bet(interaction, bet):
            return


        # Slot symbols with weights
        symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
        weights = [30, 25, 20, 15, 8, 2]  # Diamond and 7 are rare
        
        # Spin the slots
        reels = random.choices(symbols, weights=weights, k=3)
        
        # Check for wins
        multiplier = 0
        result_msg = ""
        
        if reels[0] == reels[1] == reels[2]:
            # Three of a kind
            if reels[0] == "7️⃣":
                multiplier = 10
                result_msg = "🎰 **JACKPOT!** 🎰"
            elif reels[0] == "💎":
                multiplier = 7
                result_msg = "💎 **DIAMONDS!** 💎"
            else:
                multiplier = 5
                result_msg = "🎉 **THREE OF A KIND!** 🎉"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            # Two of a kind
            multiplier = 2
            result_msg = "✨ **TWO OF A KIND!** ✨"


        # Calculate winnings
        if multiplier > 0:
            winnings = bet * multiplier
            profit = winnings - bet
            await self.bot.db.update_user_balance(interaction.user.id, profit)
            
            embed = discord.Embed(
                title="🎰 Slot Machine",
                description=f"**[ {' | '.join(reels)} ]**\n\n{result_msg}\n\nYou won **${winnings:,}** (${profit:,} profit)!",
                color=discord.Color.green()
            )
        else:
            await self.bot.db.update_user_balance(interaction.user.id, -bet)
            
            embed = discord.Embed(
                title="🎰 Slot Machine",
                description=f"**[ {' | '.join(reels)} ]**\n\nNo match! You lost **${bet:,}**",
                color=discord.Color.red()
            )


        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'slots_win' if multiplier > 0 else 'slots_loss',
            profit if multiplier > 0 else -bet,
            f'Slots: {" ".join(reels)}'
        )


        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="blackjack", description="Play blackjack against the dealer")
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        """Blackjack game"""
        if not await self._check_bet(interaction, bet):
            return


        # Card values
        cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        def card_value(card):
            if card in ['J', 'Q', 'K']:
                return 10
            elif card == 'A':
                return 11
            return int(card)
        
        def hand_value(hand):
            value = sum(card_value(c) for c in hand)
            aces = hand.count('A')
            while value > 21 and aces:
                value -= 10
                aces -= 1
            return value


        # Deal initial hands
        player_hand = [random.choice(cards), random.choice(cards)]
        dealer_hand = [random.choice(cards), random.choice(cards)]
        
        player_value = hand_value(player_hand)
        dealer_value = hand_value(dealer_hand)
        
        # Check for instant blackjack
        if player_value == 21:
            winnings = int(bet * 1.5)
            await self.bot.db.update_user_balance(interaction.user.id, winnings)
            
            embed = discord.Embed(
                title="🃏 Blackjack!",
                description=f"**Your hand:** {' '.join(player_hand)} (21)\n**Dealer:** {dealer_hand[0]} ?\n\n🎉 **BLACKJACK!** You won **${winnings:,}**!",
                color=discord.Color.gold()
            )
            
            await self.bot.db.log_transaction(
                interaction.user.id,
                interaction.guild.id if interaction.guild else 0,
                'blackjack_win',
                winnings,
                'Blackjack natural 21'
            )
            
            await interaction.response.send_message(embed=embed)
            return


        # Simple AI: dealer hits until 17
        while dealer_value < 17:
            dealer_hand.append(random.choice(cards))
            dealer_value = hand_value(dealer_hand)


        # Determine winner
        won = False
        result_msg = ""
        
        if dealer_value > 21:
            won = True
            result_msg = "🎉 Dealer busted! You win!"
        elif player_value > dealer_value:
            won = True
            result_msg = "🎉 You beat the dealer!"
        elif player_value == dealer_value:
            result_msg = "🤝 Push! Bet returned"
            await interaction.response.send_message(
                f"**Your hand:** {' '.join(player_hand)} ({player_value})\n"
                f"**Dealer:** {' '.join(dealer_hand)} ({dealer_value})\n\n{result_msg}",
                ephemeral=False
            )
            return
        else:
            result_msg = "😔 Dealer wins!"


        if won:
            await self.bot.db.update_user_balance(interaction.user.id, bet)
            color = discord.Color.green()
        else:
            await self.bot.db.update_user_balance(interaction.user.id, -bet)
            color = discord.Color.red()


        embed = discord.Embed(
            title="🃏 Blackjack",
            description=f"**Your hand:** {' '.join(player_hand)} ({player_value})\n"
                       f"**Dealer:** {' '.join(dealer_hand)} ({dealer_value})\n\n"
                       f"{result_msg}\n{'Won' if won else 'Lost'} **${bet:,}**",
            color=color
        )


        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'blackjack_win' if won else 'blackjack_loss',
            bet if won else -bet,
            f'Blackjack: Player {player_value} vs Dealer {dealer_value}'
        )


        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="dice", description="Roll dice and bet on the outcome")
    @app_commands.describe(
        bet="Amount to bet",
        prediction="Predict: low (2-6), medium (7-8), or high (9-12)"
    )
    @app_commands.choices(prediction=[
        app_commands.Choice(name="Low (2-6) - 2x", value="low"),
        app_commands.Choice(name="Medium (7-8) - 3x", value="medium"),
        app_commands.Choice(name="High (9-12) - 2x", value="high")
    ])
    async def dice(self, interaction: discord.Interaction, bet: int, prediction: str):
        """Dice betting game"""
        if not await self._check_bet(interaction, bet):
            return


        # Roll two dice
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2


        # Determine range
        actual_range = "low" if total <= 6 else "medium" if total <= 8 else "high"
        
        # Check win
        won = actual_range == prediction
        
        multipliers = {"low": 2, "medium": 3, "high": 2}
        
        if won:
            winnings = bet * multipliers[prediction]
            profit = winnings - bet
            await self.bot.db.update_user_balance(interaction.user.id, profit)
            
            embed = discord.Embed(
                title="🎲 Dice Roll - YOU WIN!",
                description=f"**Rolled:** {die1} + {die2} = **{total}**\n\n"
                           f"Range: **{actual_range.upper()}**\n"
                           f"You predicted **{prediction.upper()}**!\n\n"
                           f"Won **${winnings:,}** (${profit:,} profit)!",
                color=discord.Color.green()
            )
        else:
            await self.bot.db.update_user_balance(interaction.user.id, -bet)
            
            embed = discord.Embed(
                title="🎲 Dice Roll - You Lost",
                description=f"**Rolled:** {die1} + {die2} = **{total}**\n\n"
                           f"Range: **{actual_range.upper()}**\n"
                           f"You predicted **{prediction.upper()}**\n\n"
                           f"Lost **${bet:,}**",
                color=discord.Color.red()
            )


        await self.bot.db.log_transaction(
            interaction.user.id,
            interaction.guild.id if interaction.guild else 0,
            'dice_win' if won else 'dice_loss',
            (bet * multipliers[prediction] - bet) if won else -bet,
            f'Dice: {die1}+{die2}={total}, predicted {prediction}, actual {actual_range}'
        )


        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(CasinoCog(bot))
