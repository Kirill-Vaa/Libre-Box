import asyncio
from datetime import UTC, datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from domain.models import SleepResult, TimeNowResult
from utils.logger import logger


class SystemService:
    def __init__(self, max_sleep_seconds: int) -> None:
        self._max_sleep_seconds = max_sleep_seconds

    async def sleep(self, seconds: float) -> SleepResult:
        capped_seconds = min(max(seconds, 0.0), float(self._max_sleep_seconds))
        await asyncio.sleep(capped_seconds)
        return SleepResult(slept_seconds=capped_seconds)

    @staticmethod
    def time_now(timezone: str) -> TimeNowResult:
        zone: tzinfo
        try:
            zone = ZoneInfo(timezone)
            resolved_timezone = timezone
        except (ZoneInfoNotFoundError, ValueError) as error:
            logger.warning(f"Unknown timezone '{timezone}', falling back to UTC: {error}")
            zone = UTC
            resolved_timezone = "UTC"

        now = datetime.now(zone)
        return TimeNowResult(
            iso=now.isoformat(),
            epoch=now.timestamp(),
            human=now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            timezone=resolved_timezone,
        )
