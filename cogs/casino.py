"""
Casino Commands - Gambling games
"""
import random
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils.logger import get_logger


class BlackjackView(discord.ui.View):
    """Interactive blackjack game view with buttons"""
    
    def __init__(self, bot, interaction, bet, player_hand, dealer_hand, cards):
        super().__init__(timeout=60)
        self.bot = bot
        self.interaction = interaction
        self.bet = bet
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.cards = cards
        self.message = None
        self.finished = False
        
    def card_value(self, card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 11
        return int(card)
    
    def hand_value(self, hand):
        value = sum(self.card_value(c) for c in hand)
        aces = hand.count('A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value
    
    def create_embed(self, show_dealer=False, result=None):
        """Create the game embed"""
        player_value = self.hand_value(self.player_hand)
        dealer_value = self.hand_value(self.dealer_hand)
        
        if show_dealer:
            dealer_cards = ' '.join(self.dealer_hand)
            dealer_display = f"{dealer_cards} ({dealer_value})"
        else:
            dealer_cards = f"{self.dealer_hand[0]} ?"
            dealer_display = dealer_cards
        
        player_cards = ' '.join(self.player_hand)
        
        embed = discord.Embed(
            title="🃏 Blackjack",
            color=discord.Color.blue() if not result else (
                discord.Color.green() if "win" in result.lower() or "blackjack" in result.lower() 
                else discord.Color.red() if "bust" in result.lower() or "lose" in result.lower() or "dealer wins" in result.lower()
                else discord.Color.gold()
            )
        )
        
        embed.add_field(
            name=f"Your Hand ({player_value})",
            value=player_cards,
            inline=False
        )
        embed.add_field(
            name="Dealer's Hand",
            value=dealer_display,
            inline=False
        )
        
        if result:
            embed.add_field(name="Result", value=result, inline=False)
        
        embed.set_footer(text=f"Bet: ${self.bet:,}")
        
        return embed
    
    async def finish_game(self, result, won=None):
        """End the game and process winnings"""
        self.finished = True
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        embed = self.create_embed(show_dealer=True, result=result)
        
        if won is True:
            await self.bot.db.update_user_balance(self.interaction.user.id, self.bet)
            await self.bot.db.log_transaction(
                self.interaction.user.id,
                self.interaction.guild.id if self.interaction.guild else 0,
                'blackjack_win',
                self.bet,
                result
            )
        elif won is False:
            await self.bot.db.update_user_balance(self.interaction.user.id, -self.bet)
            await self.bot.db.log_transaction(
                self.interaction.user.id,
                self.interaction.guild.id if self.interaction.guild else 0,
                'blackjack_loss',
                -self.bet,
                result
            )
        # If won is None, it's a push (no money changes hands)
        
        await self.message.edit(embed=embed, view=self)
        self.stop()
    
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🎴")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        # Draw a card
        self.player_hand.append(random.choice(self.cards))
        player_value = self.hand_value(self.player_hand)
        
        if player_value > 21:
            # Busted
            await interaction.response.defer()
            await self.finish_game(f"💥 **BUST!** You went over 21. You lost **${self.bet:,}**", won=False)
        elif player_value == 21:
            # Got 21, auto-stand
            await interaction.response.defer()
            await self.stand_action()
        else:
            # Update the display
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def stand_action(self):
        """Process standing"""
        # Dealer plays
        while self.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(random.choice(self.cards))
        
        player_value = self.hand_value(self.player_hand)
        dealer_value = self.hand_value(self.dealer_hand)
        
        if dealer_value > 21:
            await self.finish_game(f"🎉 **DEALER BUST!** You won **${self.bet:,}**!", won=True)
        elif player_value > dealer_value:
            await self.finish_game(f"🎉 **YOU WIN!** You beat the dealer! Won **${self.bet:,}**", won=True)
        elif player_value == dealer_value:
            await self.finish_game(f"🤝 **PUSH!** Tie game - bet returned", won=None)
        else:
            await self.finish_game(f"😔 **DEALER WINS!** Lost **${self.bet:,}**", won=False)
    
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await interaction.response.defer()
        await self.stand_action()
    
    @discord.ui.button(label="Double Down", style=discord.ButtonStyle.success, emoji="💰")
    async def double_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        # Check if user has enough money
        user = await self.bot.db.get_user(interaction.user.id, interaction.user.name, interaction.user.discriminator)
        if user.balance < self.bet:
            await interaction.response.send_message("❌ Not enough money to double down!", ephemeral=True)
            return
        
        # Double the bet
        self.bet *= 2
        
        # Draw one card and stand
        self.player_hand.append(random.choice(self.cards))
        player_value = self.hand_value(self.player_hand)
        
        await interaction.response.defer()
        
        if player_value > 21:
            await self.finish_game(f"💥 **BUST!** You went over 21 after doubling down. Lost **${self.bet:,}**", won=False)
        else:
            await self.stand_action()
    
    async def on_timeout(self):
        """Handle timeout"""
        if not self.finished:
            for item in self.children:
                item.disabled = True
            embed = self.create_embed(show_dealer=True, result="⏰ Game timed out - bet returned")
            if self.message:
                await self.message.edit(embed=embed, view=self)


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
        """Interactive blackjack game with Hit/Stand/Double Down"""
        if not await self._check_bet(interaction, bet):
            return

        # Card deck
        cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        # Deal initial hands
        player_hand = [random.choice(cards), random.choice(cards)]
        dealer_hand = [random.choice(cards), random.choice(cards)]
        
        # Create the view
        view = BlackjackView(self.bot, interaction, bet, player_hand, dealer_hand, cards)
        
        # Check for instant blackjack
        if view.hand_value(player_hand) == 21:
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
        
        # Send initial game state with buttons
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

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