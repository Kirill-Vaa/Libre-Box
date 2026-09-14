import asyncio
import sys

from app import Application
from config.settings import settings
from utils.logger import logger


async def main() -> None:
    application = Application(settings)
    try:
        await application.setup()
        await application.run()
    except Exception as error:
        logger.exception(f"Fatal error during MCP service execution: {error}")
        raise
    finally:
        await application.shutdown()


def _execute() -> None:
    if sys.platform != "win32":
        try:
            import uvloop

            uvloop.run(main())
            return
        except ImportError:
            logger.info("uvloop not available, falling back to default asyncio event loop")

    asyncio.run(main())


if __name__ == "__main__":
    try:
        _execute()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
