import asyncio
from pathlib import Path

from config.constants import FILE_READ_BINARY_SNIFF_BYTES
from domain.exceptions import WorkspaceFileError
from domain.models import DirectoryResult, DirectoryTreeResult, FileEditResult, FileReadResult, FileSearchMode, FileSearchResult, FileWriteResult, TreeNode
from domain.path_resolver import PathResolver
from utils.logger import logger


class FileService:
    def __init__(self, path_resolver: PathResolver, search_root: Path) -> None:
        self._path_resolver = path_resolver
        self._search_root = search_root.resolve()

    async def read(self, path: str, offset: int, limit: int, encoding: str) -> FileReadResult:
        target = self._path_resolver.resolve(path)
        return await asyncio.to_thread(self._read_sync, target, path, offset, limit, encoding)

    async def write(self, path: str, content: str, create_dirs: bool, encoding: str) -> FileWriteResult:
        target = self._path_resolver.resolve(path)
        return await asyncio.to_thread(self._write_sync, target, content, create_dirs, encoding)

    async def edit(self, path: str, old_string: str, new_string: str, replace_all: bool, encoding: str) -> FileEditResult:
        target = self._path_resolver.resolve(path)
        return await asyncio.to_thread(self._edit_sync, target, path, old_string, new_string, replace_all, encoding)

    async def search(self, pattern: str, path: str, glob: str | None, mode: FileSearchMode, max_results: int) -> FileSearchResult:
        root = self._path_resolver.resolve(path)
        if mode == "files":
            command = ["fd", "--glob", "--hidden", "--no-ignore", "--max-results", str(max_results), pattern, str(root)]
            success_codes = (0,)
        else:
            command = ["rg", "--line-number", "--no-heading", "--color", "never", "--max-count", str(max_results)]
            if glob is not None:
                command += ["--glob", glob]
            command += [pattern, str(root)]
            success_codes = (0, 1)

        try:
            process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        except OSError as error:
            raise WorkspaceFileError(f"Search tool unavailable ({command[0]}): {error}") from error

        stdout_bytes, stderr_bytes = await process.communicate()
        if process.returncode not in success_codes:
            stderr_text = stderr_bytes.decode(errors="replace").strip()
            logger.warning(f"Search command failed tool={command[0]} code={process.returncode} stderr={stderr_text[:200]!r}")
            raise WorkspaceFileError(f"Search failed ({command[0]}): {stderr_text or f'exit code {process.returncode}'}")

        matches = stdout_bytes.decode(errors="replace").splitlines()[:max_results]
        return FileSearchResult(matches=matches)

    async def create_directory(self, path: str, parents: bool) -> DirectoryResult:
        target = self._path_resolver.resolve(path)
        await asyncio.to_thread(target.mkdir, parents=parents, exist_ok=True)
        return DirectoryResult(path=str(target))

    async def tree(self, path: str, max_depth: int, show_hidden: bool, show_sizes: bool) -> DirectoryTreeResult:
        target = self._path_resolver.resolve(path)
        node = await asyncio.to_thread(self._build_node, target, max_depth, show_hidden, show_sizes)
        return DirectoryTreeResult(root=node)

    @staticmethod
    def _read_sync(target: Path, path: str, offset: int, limit: int, encoding: str) -> FileReadResult:
        if not target.is_file():
            raise WorkspaceFileError(f"File not found: {path}")

        raw_bytes = target.read_bytes()
        if b"\x00" in raw_bytes[:FILE_READ_BINARY_SNIFF_BYTES]:
            return FileReadResult(path=str(target), content="", is_binary=True, size_bytes=len(raw_bytes), line_count=0)

        lines = raw_bytes.decode(encoding, errors="replace").splitlines()
        selected = lines[offset : offset + limit]
        numbered = "\n".join(f"{offset + index + 1}\t{line}" for index, line in enumerate(selected))
        return FileReadResult(path=str(target), content=numbered, is_binary=False, size_bytes=len(raw_bytes), line_count=len(lines))

    @staticmethod
    def _write_sync(target: Path, content: str, create_dirs: bool, encoding: str) -> FileWriteResult:
        if create_dirs:
            target.parent.mkdir(parents=True, exist_ok=True)

        data = content.encode(encoding)
        target.write_bytes(data)
        return FileWriteResult(path=str(target), bytes_written=len(data))

    @staticmethod
    def _edit_sync(target: Path, path: str, old_string: str, new_string: str, replace_all: bool, encoding: str) -> FileEditResult:
        if not target.is_file():
            raise WorkspaceFileError(f"File not found: {path}")

        try:
            text = target.read_text(encoding=encoding)
        except UnicodeDecodeError as error:
            raise WorkspaceFileError(f"Cannot edit non-text file {path}: {error}") from error

        occurrences = text.count(old_string)
        if occurrences == 0:
            raise WorkspaceFileError(f"old_string not found in {path}")
        if occurrences > 1 and not replace_all:
            raise WorkspaceFileError(f"old_string is not unique in {path} ({occurrences} matches); pass replace_all=true")

        updated = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
        target.write_text(updated, encoding=encoding)
        return FileEditResult(path=str(target), replacements=occurrences if replace_all else 1)

    def _build_node(self, target: Path, depth_remaining: int, show_hidden: bool, show_sizes: bool) -> TreeNode:
        if not target.is_dir():
            size_bytes = target.stat().st_size if show_sizes else 0
            return TreeNode(name=target.name, path=str(target), is_dir=False, size_bytes=size_bytes, children=[])

        children: list[TreeNode] = []
        total_bytes = 0
        for entry in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            if not show_hidden and entry.name.startswith("."):
                continue
            if depth_remaining > 0:
                child = self._build_node(entry, depth_remaining - 1, show_hidden, show_sizes)
                children.append(child)
                total_bytes += child.size_bytes
            elif show_sizes:
                total_bytes += self._directory_size(entry) if entry.is_dir() else entry.stat().st_size

        return TreeNode(name=target.name, path=str(target), is_dir=True, size_bytes=total_bytes, children=children)

    @staticmethod
    def _directory_size(target: Path) -> int:
        return sum(item.stat().st_size for item in target.rglob("*") if item.is_file())
