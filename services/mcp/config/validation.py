from typing import Final

from config.settings import AppSettings
from utils.logger import logger


_VALID_LOG_LEVELS: Final[frozenset[str]] = frozenset({"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"})
_MINIMUM_PORT: Final[int] = 1
_MAXIMUM_PORT: Final[int] = 65535


class ConfigurationError(RuntimeError):
    pass


def validate_settings(application_settings: AppSettings) -> None:
    errors: list[str] = []

    for port_name, port_value in (("mcp_port", application_settings.mcp_port), ("auth_port", application_settings.auth_port)):
        if not _MINIMUM_PORT <= port_value <= _MAXIMUM_PORT:
            errors.append(f"{port_name} must be between {_MINIMUM_PORT} and {_MAXIMUM_PORT}, got {port_value}")

    if application_settings.mcp_port == application_settings.auth_port:
        errors.append(f"mcp_port and auth_port must differ, both are {application_settings.mcp_port}")

    for limit_name, limit_value in (
        ("default_command_timeout_seconds", application_settings.default_command_timeout_seconds),
        ("output_char_limit", application_settings.output_char_limit),
        ("session_idle_ttl_seconds", application_settings.session_idle_ttl_seconds),
    ):
        if limit_value <= 0:
            errors.append(f"{limit_name} must be positive, got {limit_value}")

    if application_settings.log_level.upper() not in _VALID_LOG_LEVELS:
        errors.append(f"log_level must be one of {sorted(_VALID_LOG_LEVELS)}, got {application_settings.log_level}")

    if not application_settings.workspace_path.is_absolute():
        errors.append(f"workspace_path must be an absolute path, got {application_settings.workspace_path}")

    if not application_settings.sandbox_container_name:
        errors.append("sandbox_container_name must not be empty")

    if not errors:
        logger.info("Configuration validated")
        return

    for validation_error in errors:
        logger.critical(f"Invalid configuration: {validation_error}")

    raise ConfigurationError(f"Configuration validation failed with {len(errors)} error(s)")
