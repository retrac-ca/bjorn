"""
Custom decorators for bot commands
"""
import functools
from discord.ext import commands
from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_user_exists(func):
    """Ensure user exists in database before command execution"""
    @functools.wraps(func)
    async def wrapper(self, interaction, *args, **kwargs):
        # Ensure user exists in database
        await self.bot.db.get_user(
            interaction.user.id,
            interaction.user.name,
            interaction.user.discriminator
        )
        return await func(self, interaction, *args, **kwargs)
    return wrapper


def require_permissions(**perms):
    """Check if user has required permissions"""
    async def predicate(interaction):
        if not interaction.guild:
            return False
        
        user_perms = interaction.user.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(user_perms, perm) != value]
        
        if missing:
            await interaction.response.send_message(
                f"❌ You need the following permissions: {', '.join(missing)}",
                ephemeral=True
            )
            return False
        return True
    
    return commands.check(predicate)


def is_owner():
    """Check if user is bot owner"""
    async def predicate(interaction):
        return await interaction.client.is_owner(interaction.user)
    return commands.check(predicate)