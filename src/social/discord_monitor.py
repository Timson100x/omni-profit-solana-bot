"""Discord Server Monitor - Parse Token Calls & Auto-Trade.

Monitored deinen Discord Server für Token Signale und führt
validated Trades automatisch aus.
"""

import asyncio
import re
from typing import Optional, List
from datetime import datetime

import discord
from discord.ext import commands

from src.core.logger import log
from src.core.config import settings
from src.signals.validator import signal_validator
from src.trading.manager import trade_manager


class TradingBotDiscord(commands.Bot):
    """Discord Bot für Trading Signal Monitoring."""
    
    # Regex für Solana Token Adressen
    TOKEN_ADDR_PATTERN = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')
    
    # Keywords für Buy Signals
    BUY_KEYWORDS = [
        'buy', 'gem', 'moon', 'pump', 'bullish', '🚀', '💎',
        'entry', 'ape', 'long', 'accumulate', 'dca',
    ]
    
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            *args,
            **kwargs
        )
        
        self.trading_channels: List[int] = self._parse_channel_ids()
        self.processed_messages: set = set()  # Avoid duplicates
        
        log.info(
            "discord_bot_initialized",
            channels=len(self.trading_channels),
        )
    
    def _parse_channel_ids(self) -> List[int]:
        """Parse Channel IDs from config."""
        if not settings.DISCORD_CHANNEL_IDS:
            return []
        
        ids_str = settings.DISCORD_CHANNEL_IDS
        return [int(id.strip()) for id in ids_str.split(',') if id.strip()]
    
    async def on_ready(self):
        """Bot connected."""
        log.info(
            "discord_connected",
            bot=self.user.name,
            guilds=len(self.guilds),
        )
        
        print("=" * 70)
        print(f"🤖 Discord Bot Online: {self.user.name}")
        print("=" * 70)
        print()
        print(f"Connected to {len(self.guilds)} servers:")
        for guild in self.guilds:
            print(f"  - {guild.name}")
        print()
        print(f"Monitoring {len(self.trading_channels)} channels for signals")
        print()
    
    async def on_message(self, message: discord.Message):
        """Process incoming messages."""
        # Skip bot messages
        if message.author.bot:
            return
        
        # Check if in monitored channel
        if message.channel.id not in self.trading_channels:
            return
        
        # Avoid duplicate processing
        msg_id = f"{message.channel.id}_{message.id}"
        if msg_id in self.processed_messages:
            return
        
        self.processed_messages.add(msg_id)
        
        # Keep cache small
        if len(self.processed_messages) > 1000:
            self.processed_messages.clear()
        
        # Log message
        log.debug(
            "discord_message",
            channel=message.channel.name,
            author=str(message.author),
            content=message.content[:100],
        )
        
        # Parse for signals
        await self._process_signal_message(message)
        
        # Process commands
        await self.process_commands(message)
    
    async def _process_signal_message(self, message: discord.Message):
        """Extract and validate token signals from message.
        
        Args:
            message: Discord message
        """
        content = message.content.lower()
        
        # Check for buy signal keywords
        has_buy_signal = any(keyword in content for keyword in self.BUY_KEYWORDS)
        
        if not has_buy_signal:
            return
        
        # Extract token addresses
        token_addresses = self.TOKEN_ADDR_PATTERN.findall(message.content)
        
        if not token_addresses:
            return
        
        log.info(
            "signal_detected",
            channel=message.channel.name,
            tokens=len(token_addresses),
            author=str(message.author),
        )
        
        # Validate and trade each token
        for token_addr in token_addresses:
            await self._validate_and_trade(
                token_addr,
                source_channel=f"discord_{message.channel.name}",
                message=message,
            )
    
    async def _validate_and_trade(
        self,
        token_address: str,
        source_channel: str,
        message: discord.Message,
    ):
        """Validate signal and execute trade if valid.
        
        Args:
            token_address: Solana token address
            source_channel: Source channel name
            message: Original Discord message
        """
        try:
            # Validate signal
            result = await signal_validator.validate_signal(
                token_address,
                source_channel=source_channel,
            )
            
            log.info(
                "signal_validated",
                token=token_address,
                valid=result.is_valid,
                score=result.score,
            )
            
            # React to message based on validation
            if result.is_valid:
                await message.add_reaction("✅")
                await message.add_reaction("🚀")
                
                # Execute trade
                if settings.ALLOW_REAL_TRANSACTIONS:
                    # TODO: Get token data from DexScreener
                    token_data = {
                        'address': token_address,
                        'name': 'UNKNOWN',
                        'price_usd': 0.0,
                    }
                    
                    analysis = {
                        'confidence': result.score / 100.0,
                        'reason': f"Validated signal (score: {result.score})",
                        'target_multiplier': 3.0,
                    }
                    
                    success = await trade_manager.execute_trade(token_data, analysis)
                    
                    if success:
                        await message.reply(
                            f"🚀 Trade executed!\n"
                            f"Token: `{token_address[:8]}...`\n"
                            f"Validation Score: {result.score}/100\n"
                            f"Target: 3x"
                        )
                else:
                    await message.reply(
                        f"✅ Signal validated ({result.score}/100)\n"
                        f"_Simulation mode - no trade executed_"
                    )
            else:
                await message.add_reaction("⚠️")
                
                # Send warning if low score
                if result.score < 50:
                    warning_msg = "\n".join(result.warnings[:3])
                    await message.reply(
                        f"⚠️  Signal rejected ({result.score}/100)\n"
                        f"```{warning_msg}```"
                    )
        
        except Exception as e:
            log.error("validation_error", token=token_address, error=str(e))
            await message.add_reaction("❌")
    
    @commands.command(name='status')
    async def status_command(self, ctx):
        """Show bot status."""
        summary = trade_manager.get_position_summary()
        val_summary = signal_validator.get_validation_summary()
        
        embed = discord.Embed(
            title="🤖 Trading Bot Status",
            color=discord.Color.green(),
            timestamp=datetime.now(),
        )
        
        embed.add_field(
            name="📊 Positions",
            value=(
                f"Open: {summary['open_positions']}\n"
                f"Closed: {summary['closed_positions']}\n"
                f"Today: {summary['trades_today']}"
            ),
            inline=True,
        )
        
        embed.add_field(
            name="🔍 Validation",
            value=(
                f"Tracked: {val_summary['tracked_signals']}\n"
                f"Multi-Channel: {val_summary['multi_channel_signals']}"
            ),
            inline=True,
        )
        
        embed.add_field(
            name="⚙️ Settings",
            value=(
                f"Real Trades: {'✅' if settings.ALLOW_REAL_TRANSACTIONS else '❌'}\n"
                f"Emergency Stop: {'🛑' if settings.EMERGENCY_STOP else '✅'}"
            ),
            inline=False,
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='validate')
    async def validate_command(self, ctx, token_address: str):
        """Manually validate a token."""
        await ctx.send(f"🔍 Validating `{token_address}`...")
        
        try:
            result = await signal_validator.validate_signal(
                token_address,
                source_channel=f"discord_manual_{ctx.author}",
            )
            
            embed = discord.Embed(
                title="🔍 Validation Result",
                color=discord.Color.green() if result.is_valid else discord.Color.red(),
            )
            
            embed.add_field(
                name="Token",
                value=f"`{token_address}`",
                inline=False,
            )
            
            embed.add_field(
                name="Valid",
                value="✅ YES" if result.is_valid else "❌ NO",
                inline=True,
            )
            
            embed.add_field(
                name="Score",
                value=f"{result.score}/100",
                inline=True,
            )
            
            # Checks
            checks_str = "\n".join([
                f"{'✅' if v else '❌'} {k}"
                for k, v in result.checks.items()
            ])
            embed.add_field(
                name="Checks",
                value=checks_str,
                inline=False,
            )
            
            # Warnings
            if result.warnings:
                warnings_str = "\n".join([f"- {w}" for w in result.warnings[:5]])
                embed.add_field(
                    name="⚠️ Warnings",
                    value=warnings_str,
                    inline=False,
                )
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Validation failed: {e}")


async def run_discord_bot():
    """Start Discord bot."""
    if not settings.DISCORD_BOT_TOKEN:
        log.error("discord_bot_no_token")
        print("❌ DISCORD_BOT_TOKEN not configured in .env.production")
        return
    
    bot = TradingBotDiscord()
    
    try:
        await bot.start(settings.DISCORD_BOT_TOKEN)
    except Exception as e:
        log.error("discord_bot_error", error=str(e))
        print(f"❌ Discord bot error: {e}")


async def main():
    """CLI Entry Point."""
    print("=" * 70)
    print("🤖 Starting Discord Trading Bot")
    print("=" * 70)
    print()
    
    if not settings.DISCORD_BOT_TOKEN:
        print("❌ Error: DISCORD_BOT_TOKEN not set")
        print()
        print("Setup:")
        print("  1. Run: python setup_discord_server.py")
        print("  2. Add bot to your server")
        print("  3. Configure .env.production")
        return
    
    if not settings.DISCORD_CHANNEL_IDS:
        print("⚠️  Warning: No channels configured")
        print("   Bot will not monitor any channels")
        print()
        print("Add to .env.production:")
        print("   DISCORD_CHANNEL_IDS=123456789,987654321")
        print()
    
    await run_discord_bot()


if __name__ == "__main__":
    asyncio.run(main())
