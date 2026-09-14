import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Final

from loguru import logger


_STDOUT_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <magenta>{extra[request_id]}</magenta> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
_FILE_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[request_id]} | {name}:{function}:{line} - {message}"
_ARCHIVE_RETENTION_DAYS: int = 14
_LOG_DIRECTORY: Final[Path] = Path(__file__).resolve().parent.parent / "logs"


logger.remove()
logger.configure(extra={"request_id": "-"})

_console_sink_id: int = logger.add(
    sys.stdout,
    level="INFO",
    format=_STDOUT_FORMAT,
    colorize=True,
    enqueue=True,
    backtrace=True,
    diagnose=True,
)


def _build_archive_path(log_file_path: Path) -> Path:
    parent_directory = log_file_path.parent
    base_stem = log_file_path.stem
    suffix = log_file_path.suffix

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    candidate_path = parent_directory / f"{base_stem}.archive.{timestamp}{suffix}.zip"

    collision_counter = 1
    while candidate_path.exists():
        candidate_path = parent_directory / f"{base_stem}.archive.{timestamp}_{collision_counter}{suffix}.zip"
        collision_counter += 1

    return candidate_path


def _archive_existing_log(log_file_path: Path) -> None:
    if not log_file_path.exists():
        return

    try:
        if log_file_path.stat().st_size == 0:
            log_file_path.unlink()
            return

        archive_path = _build_archive_path(log_file_path)
        with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive_file:
            archive_file.write(log_file_path, arcname=log_file_path.name)

        log_file_path.unlink()
        logger.info(f"Archived previous log file to {archive_path.name}")
    except OSError as error:
        logger.warning(f"Failed to archive log file {log_file_path}: {error}")


def _purge_stale_archives(log_file_path: Path) -> None:
    log_directory = log_file_path.parent
    if not log_directory.exists():
        return

    expiration_threshold = datetime.now() - timedelta(days=_ARCHIVE_RETENTION_DAYS)
    archive_pattern = f"{log_file_path.stem}.archive.*{log_file_path.suffix}.zip"

    for archive_path in log_directory.glob(archive_pattern):
        try:
            modified_at = datetime.fromtimestamp(archive_path.stat().st_mtime)
        except OSError as error:
            logger.warning(f"Failed to stat archive {archive_path}: {error}")
            continue

        if modified_at >= expiration_threshold:
            continue

        try:
            archive_path.unlink()
            logger.debug(f"Removed stale log archive {archive_path.name}")
        except OSError as error:
            logger.warning(f"Failed to remove stale archive {archive_path}: {error}")


def configure_file_sink(log_level: str = "DEBUG", serialize: bool = False) -> None:
    _LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    log_file_path = _LOG_DIRECTORY / "mcp.log"

    _archive_existing_log(log_file_path)
    _purge_stale_archives(log_file_path)

    logger.add(
        log_file_path,
        level=log_level,
        format=_FILE_FORMAT,
        serialize=serialize,
        rotation="100 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )


def set_console_level(log_level: str) -> None:
    global _console_sink_id
    logger.remove(_console_sink_id)
    _console_sink_id = logger.add(
        sys.stdout,
        level=log_level,
        format=_STDOUT_FORMAT,
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
