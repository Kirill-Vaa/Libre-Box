from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from config.settings import settings
from config.constants import FILE_READ_DEFAULT_LIMIT, FILE_SEARCH_DEFAULT_MAX_RESULTS
from domain.models import DirectoryResult, DirectoryTreeResult, FileEditResult, FileReadResult, FileSearchMode, FileSearchResult, FileWriteResult
from services.container import ServiceContainer


def register_file_tools(mcp: MCPServer, container: ServiceContainer) -> None:
    @mcp.tool(description="Read a text file from the sandbox workspace and return its content with 1-based line-number prefixes; binary files are detected and returned without content.")
    async def file_read(
        path: Annotated[str, Field(description="File path, relative to the workspace or absolute inside /root/data")],
        offset: Annotated[int, Field(description="0-based line index to start reading from", ge=0)] = 0,
        limit: Annotated[int, Field(description="Maximum number of lines to return", ge=1, le=settings.output_char_limit)] = FILE_READ_DEFAULT_LIMIT,
        encoding: Annotated[str, Field(description="Text encoding used to decode the file")] = "utf-8",
    ) -> FileReadResult:
        return await container.file_service.read(path=path, offset=offset, limit=limit, encoding=encoding)

    @mcp.tool(description="Write the full content of a text file in the sandbox workspace, overwriting any existing file and optionally creating parent directories.")
    async def file_write(
        path: Annotated[str, Field(description="File path, relative to the workspace or absolute inside /root/data")],
        content: Annotated[str, Field(description="Full file content to write")],
        create_dirs: Annotated[bool, Field(description="Create parent directories when they do not exist")] = True,
        encoding: Annotated[str, Field(description="Text encoding used to encode the content")] = "utf-8",
    ) -> FileWriteResult:
        return await container.file_service.write(path=path, content=content, create_dirs=create_dirs, encoding=encoding)

    @mcp.tool(description="Replace exact text within an existing workspace file; by default the match must be unique, set replace_all to replace every occurrence.")
    async def file_edit(
        path: Annotated[str, Field(description="File path, relative to the workspace or absolute inside /root/data")],
        old_string: Annotated[str, Field(description="Exact text to find and replace")],
        new_string: Annotated[str, Field(description="Replacement text")],
        replace_all: Annotated[bool, Field(description="Replace every occurrence instead of requiring a unique match")] = False,
        encoding: Annotated[str, Field(description="Text encoding used to read and write the file")] = "utf-8",
    ) -> FileEditResult:
        return await container.file_service.edit(path=path, old_string=old_string, new_string=new_string, replace_all=replace_all, encoding=encoding)

    @mcp.tool(description="Search the workspace with ripgrep (content mode, regex inside files) or fd (files mode, glob against file names), returning up to max_results lines or paths.")
    async def file_search(
        pattern: Annotated[str, Field(description="Regular expression matched inside files (content mode) or glob matched against file names, e.g. *.txt (files mode)")],
        path: Annotated[str, Field(description="Directory to search within, relative to the workspace")] = ".",
        glob: Annotated[str | None, Field(description="Optional glob filter applied to file names in content mode; ignored in files mode where pattern is already a glob")] = None,
        mode: Annotated[FileSearchMode, Field(description="content searches inside files, files matches file names")] = "content",
        max_results: Annotated[int, Field(description="Maximum number of results to return", ge=1, le=10000)] = FILE_SEARCH_DEFAULT_MAX_RESULTS,
    ) -> FileSearchResult:
        return await container.file_service.search(pattern=pattern, path=path, glob=glob, mode=mode, max_results=max_results)

    @mcp.tool(description="Create a directory in the sandbox workspace, creating intermediate directories by default and succeeding if it already exists.")
    async def directory_create(
        path: Annotated[str, Field(description="Directory path, relative to the workspace or absolute inside /root/data")],
        parents: Annotated[bool, Field(description="Create intermediate directories as needed")] = True,
    ) -> DirectoryResult:
        return await container.file_service.create_directory(path=path, parents=parents)

    @mcp.tool(description="Return a recursive tree of the workspace up to a depth limit, with per-entry sizes and optional hidden entries.")
    async def directory_tree(
        path: Annotated[str, Field(description="Directory to walk, relative to the workspace")] = ".",
        max_depth: Annotated[int, Field(description="Maximum recursion depth below the starting directory", ge=0, le=20)] = 5,
        show_hidden: Annotated[bool, Field(description="Include entries whose name starts with a dot")] = True,
        show_sizes: Annotated[bool, Field(description="Compute file and aggregate directory sizes")] = True,
    ) -> DirectoryTreeResult:
        return await container.file_service.tree(path=path, max_depth=max_depth, show_hidden=show_hidden, show_sizes=show_sizes)
