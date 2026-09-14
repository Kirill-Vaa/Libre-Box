from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


FileSearchMode = Literal["content", "files"]
SignalName = Literal["CONT", "HUP", "INT", "KILL", "QUIT", "STOP", "TERM", "USR1", "USR2"]


class ShellResult(BaseModel):
    stdout: str = Field(description="Captured standard output, truncated when it exceeds the output limit")
    stderr: str = Field(description="Captured standard error, truncated when it exceeds the output limit")
    exit_code: int | None = Field(description="Process exit code, or null when the command was killed before reporting one")
    truncated: bool = Field(description="True when stdout or stderr was truncated to fit the output limit")
    duration_ms: int = Field(description="Wall-clock execution time in milliseconds")
    timed_out: bool = Field(description="True when the command exceeded its timeout and was terminated")


class SessionInfo(BaseModel):
    session_id: str = Field(description="Opaque identifier used to address this interactive shell session")
    cwd: str = Field(description="Current working directory of the session")
    created_at: datetime = Field(description="UTC timestamp when the session was created")
    last_used_at: datetime = Field(description="UTC timestamp of the most recent activity in the session")


class SessionExecutionResult(BaseModel):
    stdout: str = Field(description="Command output captured from the session, truncated when it exceeds the output limit")
    exit_code: int | None = Field(description="Command exit code, or null when the command timed out before completing")
    cwd: str = Field(description="Working directory after the command completed")
    truncated: bool = Field(description="True when the output was truncated to fit the output limit")
    timed_out: bool = Field(description="True when the command exceeded its timeout")


class SessionInputResult(BaseModel):
    output: str = Field(description="Session output captured after the input was delivered, truncated when it exceeds the output limit")
    exit_code: int | None = Field(description="Exit code of the command that was awaiting input, or null when it is still running")
    cwd: str = Field(description="Working directory of the session after the input was processed")
    truncated: bool = Field(description="True when the output was truncated to fit the output limit")
    completed: bool = Field(description="True when the command that was awaiting input finished after receiving it")


class OkResult(BaseModel):
    ok: bool = Field(description="True when the operation completed successfully")


class BackgroundProcessInfo(BaseModel):
    process_id: str = Field(description="Opaque identifier used to address this background process")
    pid: int = Field(description="Process id of the sandbox session leader that owns the command's process group")
    command: str = Field(description="Shell command that was launched")
    status: Literal["running", "exited"] = Field(description="Whether the process is still running or has already exited")
    exit_code: int | None = Field(default=None, description="Exit code once the process has exited, otherwise null")
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="UTC timestamp when the process was launched")


class BackgroundTailResult(BaseModel):
    process_id: str = Field(description="Opaque identifier of the background process")
    content: str = Field(description="Tail of the process log output")
    total_bytes: int = Field(description="Total size of the process log in bytes")
    next_offset: int = Field(description="Byte offset to pass as offset_bytes on the next tail call to resume reading")


class BackgroundWaitResult(BaseModel):
    process_id: str = Field(description="Opaque identifier of the background process")
    status: Literal["running", "exited"] = Field(description="Process status when waiting returned; still running when the wait timed out")
    exit_code: int | None = Field(description="Exit code once the process has exited, otherwise null")
    tail: str = Field(description="Tail of the process log captured when waiting returned")


class BackgroundListResult(BaseModel):
    processes: list[BackgroundProcessInfo] = Field(description="Current status of every tracked background process")


class FileReadResult(BaseModel):
    path: str = Field(description="Absolute path of the file that was read")
    content: str = Field(description="File content with 1-based line-number prefixes, empty for binary files")
    is_binary: bool = Field(description="True when the file was detected as binary and left undecoded")
    size_bytes: int = Field(description="Total file size in bytes")
    line_count: int = Field(description="Total number of lines in the file")


class FileWriteResult(BaseModel):
    path: str = Field(description="Absolute path of the file that was written")
    bytes_written: int = Field(description="Number of bytes written to the file")


class FileEditResult(BaseModel):
    path: str = Field(description="Absolute path of the file that was edited")
    replacements: int = Field(description="Number of occurrences that were replaced")


class FileSearchResult(BaseModel):
    matches: list[str] = Field(description="Matching lines in content mode, or matching file paths in files mode")


class DirectoryResult(BaseModel):
    path: str = Field(description="Absolute path of the directory")


class TreeNode(BaseModel):
    name: str = Field(description="Entry name")
    path: str = Field(description="Absolute path of the entry")
    is_dir: bool = Field(description="True when the entry is a directory")
    size_bytes: int = Field(description="File size, or aggregate size of the subtree for directories")
    children: list[TreeNode] = Field(default_factory=list, description="Child entries, present only for directories within the depth limit")


class DirectoryTreeResult(BaseModel):
    root: TreeNode = Field(description="Root node of the workspace directory tree")


class SleepResult(BaseModel):
    slept_seconds: float = Field(description="Number of seconds actually slept")


class TimeNowResult(BaseModel):
    iso: str = Field(description="Current time as an ISO 8601 string in the requested timezone")
    epoch: float = Field(description="Current time as seconds since the Unix epoch")
    human: str = Field(description="Human-readable rendering of the current time")
    timezone: str = Field(description="Timezone the time is expressed in")
