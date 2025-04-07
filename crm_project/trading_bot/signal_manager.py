"""
Module for processing trading signals
"""

import logging
from zoneinfo import ZoneInfo
from django.utils import timezone
import pytz
from crm_project.settings import TIME_ZONE
from signals.models import SeasonalSignal
from trading_bot.models import BotSeasonalSignal
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalManager:
    """
    Class for processing trading signals
    """

    def __init__(self):
        # Get local timezone from Django settings
        self.local_tz = ZoneInfo(TIME_ZONE) 
        # Log timezone information during initialization

    def check_signals(self):
        """
        Check all signals, create new ones and update existing
        BotSeasonalSignal.

        Returns:
            tuple: (int, int) - (number of created signals,
                                number of updated)
        """
        created_count = 0
        updated_count = 0
        current_year = timezone.now().year
        current_time = timezone.now()
        logger.info("=" * 20 + f"Starting signal check. Current time: {current_time} " + "=" * 20)

        # Get all seasonal signals
        seasonal_signals = SeasonalSignal.objects.all()
        logger.info(f"Found seasonal signals: {seasonal_signals.count()}")

        for signal in seasonal_signals:
            try:
                logger.info("-"*20)
                logger.info(
                    f"Processing signal: {signal} " f"(Magic: {signal.magic_number})"
                )

                # Check existing signals
                existing_signals = BotSeasonalSignal.objects.filter(
                    signal=signal, entry_date__gt=current_time
                )

                if existing_signals.exists():
                    # Update existing signals
                    updated = self.update_bot_signals(signal)
                    updated_count += updated
                    logger.info(f"Updated {updated} signals for {signal}")
                else:
                    # Create new signal
                    if self._process_signal(signal, current_year):
                        created_count += 1
                logger.info("-"*20)
            except Exception as e:
                logger.error(f"Error processing signal {signal}: {e}")

        logger.info(
            f"Signal check completed. "
            f"Created: {created_count}, Updated: {updated_count}"
        )
        logger.info("=" * 20 + " Finished processing signals" + "=" * 20)
        return created_count, updated_count

    def update_bot_signals(self, seasonal_signal: SeasonalSignal) -> int:
        """
        Updates all related BotSeasonalSignal when SeasonalSignal changes.

        Args:
            seasonal_signal: Modified seasonal signal

        Returns:
            int: Number of updated signals
        """
        updated_count = 0
        current_time = timezone.now()

        logger.info(f"Starting BotSeasonalSignal update for {seasonal_signal}")

        # Get all related BotSeasonalSignal
        bot_signals = BotSeasonalSignal.objects.filter(
            signal=seasonal_signal,
            entry_date__gt=current_time,  # Only future signals
        )

        for bot_signal in bot_signals:
            try:
                # Create new dates in fixed timezone UTC+1
                entry_date = datetime(
                    year=bot_signal.entry_date.year,
                    month=seasonal_signal.entry_month,
                    day=seasonal_signal.entry_day,
                    hour=seasonal_signal.open_time.hour,
                    minute=seasonal_signal.open_time.minute,
                    tzinfo=self.local_tz
                )

                exit_date = datetime(
                    year=bot_signal.exit_date.year,
                    month=seasonal_signal.takeprofit_month,
                    day=seasonal_signal.takeprofit_day,
                    hour=seasonal_signal.close_time.hour,
                    minute=seasonal_signal.close_time.minute,
                    tzinfo=self.local_tz
                )

                # Check if exit date needs to be moved to next year
                if exit_date < entry_date:
                    exit_date = datetime(
                        year=bot_signal.exit_date.year + 1,
                        month=seasonal_signal.takeprofit_month,
                        day=seasonal_signal.takeprofit_day,
                        hour=seasonal_signal.close_time.hour,
                        minute=seasonal_signal.close_time.minute,
                        tzinfo=self.local_tz
                    )

                # Update dates only if they changed
                if (
                    bot_signal.entry_date != entry_date
                    or bot_signal.exit_date != exit_date
                ):
                    bot_signal.entry_date = entry_date
                    bot_signal.exit_date = exit_date
                    bot_signal.save()

                    logger.info(f"Updated BotSeasonalSignal {bot_signal}:")
                    logger.info(f"New entry date (UTC+1): {entry_date}")
                    logger.info(f"New exit date (UTC+1): {exit_date}")
                    updated_count += 1

            except Exception as e:
                logger.error(f"Error updating BotSeasonalSignal {bot_signal}: {e}")

        logger.info(
            f"BotSeasonalSignal update completed. "
            f"Updated signals: {updated_count}"
        )
        return updated_count

    def _process_signal(self, signal: SeasonalSignal, current_year: int) -> bool:
        """
        Process individual signal

        Args:
            signal: Seasonal signal to process
            current_year: Current year

        Returns:
            bool: True if new signal was created, False otherwise
        """
        # Check if BotSeasonalSignal exists for current year and magic_number
        existing_bot_signal = BotSeasonalSignal.objects.filter(
            signal=signal,
            signal__magic_number=signal.magic_number,  # Add filter by magic_number
            created_at__year=current_year,
        ).exists()

        if existing_bot_signal:
            logger.info(
                f"Signal {signal} (Magic: {signal.magic_number}) already exists for year {current_year}"
            )
            return False

        # Get current time (UTC)
        current_time = datetime.now(self.local_tz)
        
        # Create entry date in fixed timezone UTC+1
        entry_date = datetime(
            year=current_year,
            month=signal.entry_month,
            day=signal.entry_day,
            hour=signal.open_time.hour,
            minute=signal.open_time.minute,
            tzinfo=self.local_tz
        )

        # Convert time to UTC for proper comparison
        logger.info(f"Entry (UTC): {entry_date} | Current time: {current_time}")
        # Compare dates in same timezone (UTC)
        if entry_date > current_time:
            self._create_bot_signal(signal, current_year)
            return True

    def _create_bot_signal(self, signal: SeasonalSignal, current_year: int):
        """
        Create trading signal

        Args:
            signal: Seasonal signal on which BotSeasonalSignal is based
            current_year: Current year
        """
        # Create entry and exit dates in fixed timezone UTC+1
        entry_date = datetime(
            year=current_year,
            month=signal.entry_month,
            day=signal.entry_day,
            hour=signal.open_time.hour,
            minute=signal.open_time.minute,
            tzinfo=self.local_tz
        )

        exit_date = datetime(
            year=current_year,
            month=signal.takeprofit_month,
            day=signal.takeprofit_day,
            hour=signal.close_time.hour,
            minute=signal.close_time.minute,
            tzinfo=self.local_tz
        )

        # If exit date is less than entry date, exit is in next year
        if exit_date < entry_date:
            exit_date = datetime(
                year=current_year + 1,
                month=signal.takeprofit_month,
                day=signal.takeprofit_day,
                hour=signal.close_time.hour,
                minute=signal.close_time.minute,
                tzinfo=self.local_tz
            )  
            logger.info(f"Exit date moved to next year: {exit_date}")

        bot_signal = BotSeasonalSignal.objects.create(
            signal=signal, entry_date=entry_date, exit_date=exit_date
        )
        logger.info("-"*20)
        logger.info(f"Created trading signal {bot_signal}:")
        logger.info(f"Entry (UTC+1): {entry_date}")
        logger.info(f"Exit (UTC+1): {exit_date}")
        logger.info(f"Magic: {signal.magic_number}")
        logger.info("-"*20)

    def create_date_with_fixed_timezone(self, year, month, day, hour, minute, 
                                        fixed_timezone='Etc/GMT-1'):
        """
        Creates date with specified timezone UTC+1 (without DST)
        
        Args:
            year: Year
            month: Month
            day: Day
            hour: Hour
            minute: Minute
            fixed_timezone: Fixed timezone (default UTC+1)
            
        Returns:
            datetime: Date in specified timezone
        """
        # Create date in specified timezone (UTC+1)
        fixed_tz = pytz.timezone(fixed_timezone)
        date_in_fixed_tz = fixed_tz.localize(
            timezone.datetime(year, month, day, hour, minute)
        )
        
        logger.info(
            f"Created date in fixed timezone {fixed_timezone}: "
            f"{date_in_fixed_tz}"
        )
        
        return date_in_fixed_tz


# Create global manager instance
signal_manager = SignalManager()
