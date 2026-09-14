from pathlib import Path
from typing import Final

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    sandbox_container_name: str = "libre-box-sandbox"
    workspace_path: Path = Path("/root/data")
    background_log_dir: str = "/root/.box/logs"
    mcp_port: int = 8080
    auth_port: int = 8081
    default_command_timeout_seconds: int = 600
    output_char_limit: int = 100000
    session_idle_ttl_seconds: int = 3600
    log_level: str = "INFO"
    log_serialize: bool = True

    jwt_secret: SecretStr | None = Field(default=None, validation_alias="JWT_SECRET")
    jwt_refresh_secret: SecretStr | None = Field(default=None, validation_alias="JWT_REFRESH_SECRET")


settings: Final[AppSettings] = AppSettings()
