from pathlib import Path

from config.settings import AppSettings
from domain.path_resolver import PathResolver
from infrastructure.docker.sandbox_client import SandboxClient
from services.background_service import BackgroundService
from services.file_service import FileService
from services.session_service import SessionService
from services.shell_service import ShellService
from services.system_service import SystemService


class ServiceContainer:
    def __init__(self, app_settings: AppSettings, sandbox_client: SandboxClient) -> None:
        workspace: Path = app_settings.workspace_path
        self.settings = app_settings
        self.sandbox_client = sandbox_client
        self.background_service = BackgroundService(sandbox_client, app_settings.background_log_dir)
        self.file_service = FileService(PathResolver(workspace), workspace)
        self.session_service = SessionService(sandbox_client, workspace, app_settings.default_command_timeout_seconds, app_settings.session_idle_ttl_seconds)
        self.shell_service = ShellService(sandbox_client, app_settings.default_command_timeout_seconds)
        self.system_service = SystemService(app_settings.default_command_timeout_seconds)
