class SandboxError(Exception):
    pass


class SandboxUnavailableError(SandboxError):
    def __init__(self, container_name: str, reason: str) -> None:
        super().__init__(f"Sandbox container '{container_name}' is unavailable: {reason}")
        self.container_name = container_name
        self.reason = reason


class SessionNotFoundError(SandboxError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session '{session_id}' not found")
        self.session_id = session_id


class SessionBrokenError(SandboxError):
    def __init__(self, session_id: str, reason: str) -> None:
        super().__init__(f"Session '{session_id}' is no longer usable: {reason}")
        self.session_id = session_id
        self.reason = reason


class ProcessNotFoundError(SandboxError):
    def __init__(self, process_id: str) -> None:
        super().__init__(f"Background process '{process_id}' not found")
        self.process_id = process_id


class PathTraversalError(SandboxError):
    def __init__(self, path: str) -> None:
        super().__init__(f"Path '{path}' escapes the workspace")
        self.path = path


class WorkspaceFileError(SandboxError):
    pass
