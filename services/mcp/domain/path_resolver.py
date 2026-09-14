from pathlib import Path

from domain.exceptions import PathTraversalError


class PathResolver:
    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root.resolve()

    @property
    def workspace_root(self) -> Path:
        return self._workspace_root

    def resolve(self, candidate: str) -> Path:
        raw_path = Path(candidate)
        combined = raw_path if raw_path.is_absolute() else self._workspace_root / raw_path
        resolved = combined.resolve()

        if resolved != self._workspace_root and self._workspace_root not in resolved.parents:
            raise PathTraversalError(candidate)

        return resolved
