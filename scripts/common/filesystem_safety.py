"""Pinned-parent filesystem operations for security-sensitive Osito tools.

The public functions in this module deliberately expose a small capability
surface: callers pin trusted directories, address children by a single relative
name, use an operating-system no-replace rename primitive, and revalidate the
configured paths before reporting success.
"""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import errno
import os
from pathlib import Path
import secrets
import stat
import sys
from typing import Any, Callable, Iterable


FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class FilesystemSafetyError(RuntimeError):
    """Raised when a filesystem operation cannot be proven safe."""


class DestinationExistsError(FilesystemSafetyError):
    """Raised when an exclusive destination already exists."""


class IdentityChangedError(FilesystemSafetyError):
    """Raised when a pinned object no longer matches its configured path."""


class PublicationOutcomeError(IdentityChangedError):
    """Raised when a final publication name may have been reached and must be preserved."""


class UnsupportedFilesystemError(FilesystemSafetyError):
    """Raised when the host cannot provide the required security properties."""


@dataclass(frozen=True)
class FileIdentity:
    """Stable identity fields used while an object remains open."""

    device: int
    inode: int
    mount_id: int | None = None


@dataclass(frozen=True)
class ChildMetadata:
    """Non-following metadata for one immediate child entry."""

    identity: FileIdentity
    kind: str
    link_count: int


@dataclass
class PinnedDirectory:
    """An open directory plus its observed identity and configured path."""

    path: Path
    handle: int
    identity: FileIdentity
    filesystem: str
    _closed: bool = False

    def close(self) -> None:
        if self._closed:
            return
        if os.name == "nt":
            if not _kernel32.CloseHandle(self.handle):
                raise FilesystemSafetyError("A pinned Windows directory handle could not be closed.")
        else:
            os.close(self.handle)
        self._closed = True

    def __enter__(self) -> "PinnedDirectory":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


_test_hook: Callable[[str, dict[str, Any]], None] | None = None


def invoke_test_hook(event: str, **details: Any) -> None:
    """Invoke the deterministic test hook when a test has installed one."""

    if _test_hook is not None:
        _test_hook(event, details)


def _validate_child_name(name: str) -> None:
    if (
        not name
        or name in {".", ".."}
        or "/" in name
        or "\\" in name
        or "\x00" in name
        or any(ord(character) < 32 for character in name)
    ):
        raise FilesystemSafetyError("Filesystem operations require one safe relative child name.")
    if os.name == "nt":
        stem = name.split(".", 1)[0].casefold()
        reserved = {"con", "prn", "aux", "nul"}
        reserved.update(f"com{index}" for index in range(1, 10))
        reserved.update(f"lpt{index}" for index in range(1, 10))
        if ":" in name or name.endswith((" ", ".")) or stem in reserved:
            raise FilesystemSafetyError(
                "Windows filesystem operations require a non-reserved child name "
                "without streams or trailing normalization characters."
            )


def _is_reparse(observation: os.stat_result) -> bool:
    return bool(getattr(observation, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def _posix_mount_id(descriptor: int) -> int | None:
    if not sys.platform.startswith("linux"):
        return None
    try:
        fdinfo_path = os.path.join(
            os.sep,
            "proc",
            "self",
            "fdinfo",
            str(descriptor),
        )
        with open(fdinfo_path, encoding="ascii") as stream:
            for line in stream:
                if line.startswith("mnt_id:"):
                    return int(line.split(":", 1)[1].strip())
    except (OSError, ValueError):
        return None
    return None


def _posix_identity(descriptor: int) -> FileIdentity:
    observation = os.fstat(descriptor)
    return FileIdentity(
        device=observation.st_dev,
        inode=observation.st_ino,
        mount_id=_posix_mount_id(descriptor),
    )


def _posix_open_directory(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path, flags)
    except OSError as exc:
        raise FilesystemSafetyError(f"Directory could not be opened without following links: {path}") from exc


def _posix_open_component_path(path: Path) -> int:
    anchor = Path(path.anchor or os.sep)
    current = _posix_open_directory(anchor)
    try:
        for name in path.relative_to(anchor).parts:
            child = os.open(
                name,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current,
            )
            os.close(current)
            current = child
        return current
    except Exception:
        os.close(current)
        raise


def _posix_open_child_directory(
    parent: PinnedDirectory,
    name: str,
    *,
    create: bool,
) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    if create:
        try:
            os.mkdir(name, mode=0o700, dir_fd=parent.handle)
        except FileExistsError as exc:
            raise DestinationExistsError(f"Directory already exists: {name}") from exc
        except OSError as exc:
            raise FilesystemSafetyError(f"Directory could not be created safely: {name}") from exc
    try:
        return os.open(name, flags, dir_fd=parent.handle)
    except OSError as exc:
        suffix = (
            f" The newly created path was left for manual inspection: {name}"
            if create
            else ""
        )
        raise FilesystemSafetyError(
            f"Directory could not be opened safely: {name}.{suffix}"
        ) from exc


if os.name == "nt":
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")

    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    FILE_LIST_DIRECTORY = 0x0001
    FILE_ADD_FILE = 0x0002
    FILE_ADD_SUBDIRECTORY = 0x0004
    FILE_READ_DATA = 0x0001
    FILE_WRITE_DATA = 0x0002
    FILE_APPEND_DATA = 0x0004
    FILE_TRAVERSE = 0x0020
    FILE_READ_ATTRIBUTES = 0x0080
    FILE_WRITE_ATTRIBUTES = 0x0100
    DELETE = 0x00010000
    SYNCHRONIZE = 0x00100000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_ATTRIBUTE_NORMAL = 0x00000080
    FILE_OPEN = 0x00000001
    FILE_CREATE = 0x00000002
    FILE_DIRECTORY_FILE = 0x00000001
    FILE_NON_DIRECTORY_FILE = 0x00000040
    FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
    FILE_OPEN_REPARSE_POINT = 0x00200000
    OBJ_CASE_INSENSITIVE = 0x00000040
    FILE_DISPOSITION_INFO_CLASS = 4
    ERROR_ALREADY_EXISTS = 183
    ERROR_FILE_EXISTS = 80

    class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    class _FILE_ID_128(ctypes.Structure):
        _fields_ = [("Identifier", ctypes.c_ubyte * 16)]

    class _FILE_ID_INFO(ctypes.Structure):
        _fields_ = [
            ("VolumeSerialNumber", ctypes.c_ulonglong),
            ("FileId", _FILE_ID_128),
        ]

    class _UNICODE_STRING(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        ]

    class _OBJECT_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(_UNICODE_STRING)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        ]

    class _IO_STATUS_BLOCK(ctypes.Structure):
        _fields_ = [
            ("Status", ctypes.c_ssize_t),
            ("Information", ctypes.c_size_t),
        ]

    class _FILE_RENAME_INFO(ctypes.Structure):
        _fields_ = [
            ("ReplaceIfExists", wintypes.BOOLEAN),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        ]

    class _FILE_DISPOSITION_INFO(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

    class _FILE_DIRECTORY_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("NextEntryOffset", wintypes.ULONG),
            ("FileIndex", wintypes.ULONG),
            ("CreationTime", ctypes.c_longlong),
            ("LastAccessTime", ctypes.c_longlong),
            ("LastWriteTime", ctypes.c_longlong),
            ("ChangeTime", ctypes.c_longlong),
            ("EndOfFile", ctypes.c_longlong),
            ("AllocationSize", ctypes.c_longlong),
            ("FileAttributes", wintypes.ULONG),
            ("FileNameLength", wintypes.ULONG),
            ("FileName", wintypes.WCHAR * 1),
        ]

    _kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION),
    ]
    _kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    _kernel32.GetFileInformationByHandleEx.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    _kernel32.GetFileInformationByHandleEx.restype = wintypes.BOOL
    _kernel32.GetVolumeInformationByHandleW.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPWSTR,
        wintypes.DWORD,
    ]
    _kernel32.GetVolumeInformationByHandleW.restype = wintypes.BOOL
    _kernel32.SetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    _kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
    _kernel32.WriteFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    _kernel32.WriteFile.restype = wintypes.BOOL
    _kernel32.ReadFile.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    _kernel32.ReadFile.restype = wintypes.BOOL
    _kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    _kernel32.FlushFileBuffers.restype = wintypes.BOOL
    _kernel32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    _kernel32.GetDriveTypeW.restype = wintypes.UINT
    _ntdll.NtCreateFile.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(_OBJECT_ATTRIBUTES),
        ctypes.POINTER(_IO_STATUS_BLOCK),
        ctypes.POINTER(ctypes.c_longlong),
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.LPVOID,
        wintypes.ULONG,
    ]
    _ntdll.NtCreateFile.restype = ctypes.c_long
    _ntdll.RtlNtStatusToDosError.argtypes = [ctypes.c_long]
    _ntdll.RtlNtStatusToDosError.restype = wintypes.ULONG
    _ntdll.NtSetInformationFile.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_IO_STATUS_BLOCK),
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.c_int,
    ]
    _ntdll.NtSetInformationFile.restype = ctypes.c_long
    _ntdll.NtQueryDirectoryFile.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.LPVOID,
        ctypes.POINTER(_IO_STATUS_BLOCK),
        wintypes.LPVOID,
        wintypes.ULONG,
        ctypes.c_int,
        wintypes.BOOLEAN,
        ctypes.POINTER(_UNICODE_STRING),
        wintypes.BOOLEAN,
    ]
    _ntdll.NtQueryDirectoryFile.restype = ctypes.c_long

    def _windows_error(message: str, code: int | None = None) -> OSError:
        return OSError(code if code is not None else ctypes.get_last_error(), message)

    def _windows_information(handle: int) -> _BY_HANDLE_FILE_INFORMATION:
        information = _BY_HANDLE_FILE_INFORMATION()
        if not _kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
            raise _windows_error("Windows could not inspect an open filesystem object.")
        return information

    def _windows_identity(handle: int) -> FileIdentity:
        information = _FILE_ID_INFO()
        if not _kernel32.GetFileInformationByHandleEx(
            handle,
            18,  # FileIdInfo
            ctypes.byref(information),
            ctypes.sizeof(information),
        ):
            raise _windows_error("Windows could not retrieve a strong filesystem identity.")
        inode = int.from_bytes(bytes(information.FileId.Identifier), "little")
        return FileIdentity(
            device=information.VolumeSerialNumber,
            inode=inode,
        )

    def _windows_filesystem(handle: int) -> str:
        buffer = ctypes.create_unicode_buffer(64)
        if not _kernel32.GetVolumeInformationByHandleW(
            handle,
            None,
            0,
            None,
            None,
            None,
            buffer,
            len(buffer),
        ):
            raise _windows_error("Windows could not identify the filesystem for a pinned directory.")
        filesystem = buffer.value.upper()
        if filesystem != "NTFS":
            raise UnsupportedFilesystemError(
                f"Windows destructive operations currently require local NTFS; "
                f"found {filesystem or 'unknown'}."
            )
        return filesystem

    def _windows_validate_handle(handle: int, *, directory: bool | None) -> None:
        information = _windows_information(handle)
        attributes = information.dwFileAttributes
        if attributes & FILE_ATTRIBUTE_REPARSE_POINT:
            raise FilesystemSafetyError("Windows reparse points and junctions are not permitted.")
        is_directory = bool(attributes & stat.FILE_ATTRIBUTE_DIRECTORY)
        if directory is True and not is_directory:
            raise FilesystemSafetyError("Expected a directory but opened another entry type.")
        if directory is False and is_directory:
            raise FilesystemSafetyError("Expected a regular file but opened a directory.")

    def _windows_open_path(path: Path) -> int:
        desired = FILE_LIST_DIRECTORY | FILE_TRAVERSE | FILE_READ_ATTRIBUTES | SYNCHRONIZE
        handle = _kernel32.CreateFileW(
            str(path),
            desired,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle == INVALID_HANDLE_VALUE:
            raise _windows_error(f"Windows could not pin directory: {path}")
        try:
            _windows_validate_handle(handle, directory=True)
            return handle
        except Exception:
            _kernel32.CloseHandle(handle)
            raise

    def _windows_open_relative(
        parent_handle: int,
        name: str,
        *,
        create: bool,
        directory: bool | None,
        delete_access: bool = False,
        write_access: bool = False,
        directory_write_access: bool = False,
        list_access: bool = True,
    ) -> int:
        name_buffer = ctypes.create_unicode_buffer(name)
        name_length = len(name.encode("utf-16-le"))
        unicode_name = _UNICODE_STRING(
            name_length,
            name_length,
            ctypes.cast(name_buffer, wintypes.LPWSTR),
        )
        attributes = _OBJECT_ATTRIBUTES(
            ctypes.sizeof(_OBJECT_ATTRIBUTES),
            parent_handle,
            ctypes.pointer(unicode_name),
            OBJ_CASE_INSENSITIVE,
            None,
            None,
        )
        handle = wintypes.HANDLE()
        status_block = _IO_STATUS_BLOCK()
        desired = FILE_READ_ATTRIBUTES | SYNCHRONIZE
        if directory is True:
            desired |= FILE_TRAVERSE
            if list_access:
                desired |= FILE_LIST_DIRECTORY
            if directory_write_access:
                desired |= FILE_ADD_FILE | FILE_ADD_SUBDIRECTORY
        else:
            desired |= FILE_READ_DATA
        if delete_access:
            desired |= DELETE
        if write_access:
            desired |= FILE_WRITE_DATA | FILE_APPEND_DATA | FILE_WRITE_ATTRIBUTES
        options = FILE_SYNCHRONOUS_IO_NONALERT | FILE_OPEN_REPARSE_POINT
        if directory is True:
            options |= FILE_DIRECTORY_FILE
        elif directory is False:
            options |= FILE_NON_DIRECTORY_FILE
        status = _ntdll.NtCreateFile(
            ctypes.byref(handle),
            desired,
            ctypes.byref(attributes),
            ctypes.byref(status_block),
            None,
            FILE_ATTRIBUTE_NORMAL,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            FILE_CREATE if create else FILE_OPEN,
            options,
            None,
            0,
        )
        if status < 0:
            winerror = int(_ntdll.RtlNtStatusToDosError(status))
            if winerror in {2, 3}:
                raise FileNotFoundError(winerror, f"Child entry was not found: {name}")
            if winerror in {ERROR_ALREADY_EXISTS, ERROR_FILE_EXISTS}:
                raise DestinationExistsError(f"Child entry already exists: {name}")
            raise OSError(winerror, f"Windows could not open child entry safely: {name}")
        numeric_handle = int(handle.value)
        try:
            _windows_validate_handle(numeric_handle, directory=directory)
            return numeric_handle
        except Exception:
            _kernel32.CloseHandle(numeric_handle)
            raise

    def _windows_open_component_path(path: Path) -> int:
        anchor = Path(path.anchor)
        if not anchor.drive or str(anchor).startswith("\\\\"):
            raise UnsupportedFilesystemError(
                "Windows destructive operations require a local fixed drive."
            )
        if _kernel32.GetDriveTypeW(str(anchor)) != 3:  # DRIVE_FIXED
            raise UnsupportedFilesystemError(
                "Windows destructive operations require a local fixed drive."
            )
        current = _windows_open_path(anchor)
        parts = path.relative_to(anchor).parts
        try:
            for index, name in enumerate(parts):
                child = _windows_open_relative(
                    current,
                    name,
                    create=False,
                    directory=True,
                    list_access=index == len(parts) - 1,
                )
                _kernel32.CloseHandle(current)
                current = child
            return current
        except Exception:
            _kernel32.CloseHandle(current)
            raise

    def _windows_write_all(handle: int, data: bytes) -> None:
        offset = 0
        while offset < len(data):
            block = data[offset : offset + 1024 * 1024]
            buffer = ctypes.create_string_buffer(block)
            written = wintypes.DWORD()
            if not _kernel32.WriteFile(
                handle,
                buffer,
                len(block),
                ctypes.byref(written),
                None,
            ):
                raise _windows_error("Windows could not write a handle-relative file.")
            if written.value == 0:
                raise FilesystemSafetyError("Windows reported a zero-length file write.")
            offset += written.value
        if not _kernel32.FlushFileBuffers(handle):
            raise _windows_error("Windows could not flush a handle-relative file.")

    def _windows_read_all(handle: int, *, max_bytes: int | None = None) -> bytes:
        chunks: list[bytes] = []
        total = 0
        while True:
            block_size = 1024 * 1024
            if max_bytes is not None:
                block_size = min(block_size, max_bytes + 1 - total)
                if block_size <= 0:
                    raise FilesystemSafetyError("File exceeded the configured size limit while reading.")
            buffer = ctypes.create_string_buffer(block_size)
            read = wintypes.DWORD()
            if not _kernel32.ReadFile(
                handle,
                buffer,
                len(buffer),
                ctypes.byref(read),
                None,
            ):
                error = ctypes.get_last_error()
                if error == 38:  # ERROR_HANDLE_EOF
                    break
                raise _windows_error("Windows could not read a handle-relative file.", error)
            if read.value == 0:
                break
            block = buffer.raw[: read.value]
            chunks.append(block)
            total += len(block)
            if max_bytes is not None and total > max_bytes:
                raise FilesystemSafetyError("File exceeded the configured size limit while reading.")
        return b"".join(chunks)

    def _windows_rename_handle(handle: int, destination_parent: int, destination_name: str) -> None:
        encoded_length = len(destination_name.encode("utf-16-le"))
        # Windows requires at least sizeof(FILE_RENAME_INFO) plus the complete
        # filename byte count, even though FileName[1] is already part of the
        # structure declaration.
        buffer_size = ctypes.sizeof(_FILE_RENAME_INFO) + encoded_length
        buffer = ctypes.create_string_buffer(buffer_size)
        information = _FILE_RENAME_INFO.from_buffer(buffer)
        information.ReplaceIfExists = False
        information.RootDirectory = destination_parent
        information.FileNameLength = encoded_length
        ctypes.memmove(
            ctypes.addressof(buffer) + _FILE_RENAME_INFO.FileName.offset,
            ctypes.create_unicode_buffer(destination_name),
            encoded_length,
        )
        status_block = _IO_STATUS_BLOCK()
        status = _ntdll.NtSetInformationFile(
            handle,
            ctypes.byref(status_block),
            buffer,
            buffer_size,
            10,  # FileRenameInformation
        )
        if status < 0:
            error = int(_ntdll.RtlNtStatusToDosError(status))
            raise _windows_error(
                "The Windows handle-relative no-replace rename failed.",
                error,
            )

    def _windows_mark_delete(handle: int) -> None:
        information = _FILE_DISPOSITION_INFO(True)
        if not _kernel32.SetFileInformationByHandle(
            handle,
            FILE_DISPOSITION_INFO_CLASS,
            ctypes.byref(information),
            ctypes.sizeof(information),
        ):
            raise _windows_error("Windows could not remove the verified entry.")

    def _windows_list_names(handle: int) -> list[str]:
        names: list[str] = []
        restart = True
        while True:
            buffer = ctypes.create_string_buffer(64 * 1024)
            status_block = _IO_STATUS_BLOCK()
            status = _ntdll.NtQueryDirectoryFile(
                handle,
                None,
                None,
                None,
                ctypes.byref(status_block),
                buffer,
                len(buffer),
                1,  # FileDirectoryInformation
                False,
                None,
                restart,
            )
            restart = False
            unsigned_status = status & 0xFFFFFFFF
            if unsigned_status == 0x80000006:  # STATUS_NO_MORE_FILES
                break
            if status < 0:
                error = int(_ntdll.RtlNtStatusToDosError(status))
                raise _windows_error("Windows could not enumerate a pinned directory.", error)
            offset = 0
            while True:
                entry = _FILE_DIRECTORY_INFORMATION.from_buffer(buffer, offset)
                name_offset = offset + _FILE_DIRECTORY_INFORMATION.FileName.offset
                name = ctypes.wstring_at(
                    ctypes.addressof(buffer) + name_offset,
                    entry.FileNameLength // ctypes.sizeof(wintypes.WCHAR),
                )
                if name not in {".", ".."}:
                    names.append(name)
                if entry.NextEntryOffset == 0:
                    break
                offset += entry.NextEntryOffset
        return names


def _identity_for_handle(handle: int) -> FileIdentity:
    if os.name == "nt":
        return _windows_identity(handle)
    return _posix_identity(handle)


def _ensure_same_boundary(parent: PinnedDirectory, child_identity: FileIdentity) -> None:
    if child_identity.device != parent.identity.device:
        raise FilesystemSafetyError("Nested filesystems and mount boundaries are not permitted.")
    if (
        parent.identity.mount_id is not None
        and child_identity.mount_id is not None
        and child_identity.mount_id != parent.identity.mount_id
    ):
        raise FilesystemSafetyError("Nested Linux mounts, including bind mounts, are not permitted.")


def pin_root(path: Path) -> PinnedDirectory:
    """Pin a lexical directory path without following its final component."""

    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        initial = lexical.stat(follow_symlinks=False)
    except OSError as exc:
        raise FilesystemSafetyError(f"Directory could not be inspected: {lexical}") from exc
    if (
        not stat.S_ISDIR(initial.st_mode)
        or stat.S_ISLNK(initial.st_mode)
        or _is_reparse(initial)
    ):
        raise FilesystemSafetyError("Repository and workspace roots must be ordinary directories.")

    if os.name == "nt":
        anchor = Path(lexical.anchor)
        if (
            not anchor.drive
            or str(anchor).startswith("\\\\")
            or _kernel32.GetDriveTypeW(str(anchor)) != 3
        ):
            raise UnsupportedFilesystemError(
                "Windows destructive operations require a local fixed drive."
            )
        try:
            handle = _windows_open_component_path(lexical)
            identity = _windows_identity(handle)
            filesystem = _windows_filesystem(handle)
        except (FilesystemSafetyError, UnsupportedFilesystemError):
            if "handle" in locals():
                _kernel32.CloseHandle(handle)
            raise
        except OSError as exc:
            if "handle" in locals():
                _kernel32.CloseHandle(handle)
            raise FilesystemSafetyError(
                f"Windows could not pin the complete directory ancestry: {lexical}"
            ) from exc
    else:
        try:
            handle = _posix_open_component_path(lexical)
        except OSError as exc:
            raise FilesystemSafetyError(
                f"Directory ancestry could not be opened without following links: {lexical}"
            ) from exc
        try:
            observation = os.fstat(handle)
            if not stat.S_ISDIR(observation.st_mode):
                raise FilesystemSafetyError("Pinned root is not a directory.")
            identity = _posix_identity(handle)
            if sys.platform.startswith("linux") and identity.mount_id is None:
                raise UnsupportedFilesystemError(
                    "Linux mount identity is unavailable; destructive operations are blocked."
                )
            filesystem = "linux" if sys.platform.startswith("linux") else sys.platform
        except Exception:
            os.close(handle)
            raise

    pinned = PinnedDirectory(lexical, handle, identity, filesystem)
    initial_device = initial.st_dev
    if (initial_device, initial.st_ino) != (identity.device, identity.inode):
        pinned.close()
        raise IdentityChangedError("Directory identity changed while it was being pinned.")
    return pinned


def revalidate_directory(directory: PinnedDirectory) -> None:
    """Reopen the configured path without following links and compare identity."""

    if directory._closed:
        raise FilesystemSafetyError("A closed directory capability cannot be revalidated.")
    reopened = pin_root(directory.path)
    try:
        if (
            reopened.identity != directory.identity
            or reopened.filesystem != directory.filesystem
        ):
            raise IdentityChangedError(f"Pinned directory path changed identity: {directory.path}")
    finally:
        reopened.close()


def open_child_directory(
    parent: PinnedDirectory,
    name: str,
    *,
    create: bool = False,
) -> PinnedDirectory:
    """Open or exclusively create one directory through a pinned parent."""

    _validate_child_name(name)
    if parent._closed:
        raise FilesystemSafetyError("A closed parent capability cannot be used.")
    try:
        if os.name == "nt":
            handle = _windows_open_relative(
                parent.handle,
                name,
                create=create,
                directory=True,
                delete_access=True,
                directory_write_access=True,
            )
            filesystem = _windows_filesystem(handle)
        else:
            handle = _posix_open_child_directory(parent, name, create=create)
            filesystem = parent.filesystem
        identity = _identity_for_handle(handle)
        _ensure_same_boundary(parent, identity)
    except Exception as exc:
        if "handle" in locals():
            if os.name == "nt":
                if create:
                    try:
                        _windows_mark_delete(handle)
                    except Exception:
                        pass
                _kernel32.CloseHandle(handle)
            else:
                os.close(handle)
        if isinstance(exc, OSError):
            raise FilesystemSafetyError(
                f"Directory could not be opened through its pinned parent: {name}. "
                + (
                    "The created path was left for manual inspection."
                    if create
                    else ""
                )
            ) from exc
        raise
    return PinnedDirectory(parent.path / name, handle, identity, filesystem)


def ensure_relative_directory(
    root: PinnedDirectory,
    parts: Iterable[str],
    *,
    create: bool,
) -> list[PinnedDirectory]:
    """Open a safe relative directory chain, optionally creating missing parts."""

    opened: list[PinnedDirectory] = []
    current = root
    try:
        for name in parts:
            _validate_child_name(name)
            if child_exists(current, name):
                child = open_child_directory(current, name)
            elif create:
                child = open_child_directory(current, name, create=True)
            else:
                raise FilesystemSafetyError(f"Required directory does not exist: {name}")
            opened.append(child)
            current = child
        return opened
    except Exception:
        for directory in reversed(opened):
            directory.close()
        raise


def child_exists(parent: PinnedDirectory, name: str) -> bool:
    """Return whether any child entry exists without following it."""

    _validate_child_name(name)
    if os.name == "nt":
        try:
            handle = _windows_open_relative(
                parent.handle,
                name,
                create=False,
                directory=None,
            )
        except FileNotFoundError:
            return False
        except OSError as exc:
            if getattr(exc, "winerror", None) in {2, 3} or exc.errno in {2, 3}:
                return False
            raise FilesystemSafetyError(f"Child entry could not be inspected safely: {name}") from exc
        else:
            _kernel32.CloseHandle(handle)
            return True
    try:
        os.stat(name, dir_fd=parent.handle, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise FilesystemSafetyError(f"Child entry could not be inspected safely: {name}") from exc


def child_identity(parent: PinnedDirectory, name: str, *, directory: bool) -> FileIdentity:
    """Open one child without following it and return its identity."""

    _validate_child_name(name)
    if os.name == "nt":
        try:
            handle = _windows_open_relative(
                parent.handle,
                name,
                create=False,
                directory=directory,
            )
        except OSError as exc:
            raise FilesystemSafetyError(
                f"Child entry could not be opened safely: {name}"
            ) from exc
        try:
            identity = _windows_identity(handle)
        except OSError as exc:
            raise FilesystemSafetyError(
                f"Child identity could not be read safely: {name}"
            ) from exc
        finally:
            _kernel32.CloseHandle(handle)
    else:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        if directory:
            flags |= getattr(os, "O_DIRECTORY", 0)
        try:
            handle = os.open(name, flags, dir_fd=parent.handle)
        except OSError as exc:
            raise FilesystemSafetyError(f"Child entry could not be opened safely: {name}") from exc
        try:
            observation = os.fstat(handle)
            if directory and not stat.S_ISDIR(observation.st_mode):
                raise FilesystemSafetyError("Expected a directory.")
            if not directory and not stat.S_ISREG(observation.st_mode):
                raise FilesystemSafetyError("Expected a regular file.")
            identity = _posix_identity(handle)
        finally:
            os.close(handle)
    _ensure_same_boundary(parent, identity)
    return identity


def list_child_names(parent: PinnedDirectory) -> list[str]:
    """Enumerate immediate child names through an already pinned directory."""

    if parent._closed:
        raise FilesystemSafetyError("A closed directory capability cannot be enumerated.")
    try:
        if os.name == "nt":
            names = _windows_list_names(parent.handle)
        else:
            names = os.listdir(parent.handle)
    except OSError as exc:
        raise FilesystemSafetyError("Pinned directory enumeration failed.") from exc
    for name in names:
        _validate_child_name(name)
    return sorted(names, key=lambda value: (value.casefold(), value))


def inspect_child(parent: PinnedDirectory, name: str) -> ChildMetadata:
    """Inspect one immediate child without following links or reparse points."""

    _validate_child_name(name)
    if os.name == "nt":
        try:
            handle = _windows_open_relative(
                parent.handle,
                name,
                create=False,
                directory=None,
            )
        except OSError as exc:
            raise FilesystemSafetyError(f"Child entry could not be opened safely: {name}") from exc
        try:
            information = _windows_information(handle)
            if information.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT:
                raise FilesystemSafetyError(
                    f"Child entry is a Windows junction or reparse point: {name}"
                )
            kind = (
                "directory"
                if information.dwFileAttributes & stat.FILE_ATTRIBUTE_DIRECTORY
                else "file"
            )
            metadata = ChildMetadata(
                identity=_windows_identity(handle),
                kind=kind,
                link_count=information.nNumberOfLinks,
            )
        finally:
            _kernel32.CloseHandle(handle)
    else:
        try:
            observation = os.stat(name, dir_fd=parent.handle, follow_symlinks=False)
        except OSError as exc:
            raise FilesystemSafetyError(f"Child entry could not be inspected safely: {name}") from exc
        if stat.S_ISLNK(observation.st_mode) or _is_reparse(observation):
            raise FilesystemSafetyError(f"Child entry is a symbolic link or reparse point: {name}")
        if stat.S_ISDIR(observation.st_mode):
            kind = "directory"
        elif stat.S_ISREG(observation.st_mode):
            kind = "file"
        else:
            raise FilesystemSafetyError(f"Child entry has an unsupported type: {name}")
        metadata = ChildMetadata(
            identity=FileIdentity(
                observation.st_dev,
                observation.st_ino,
                parent.identity.mount_id,
            ),
            kind=kind,
            link_count=observation.st_nlink,
        )
    _ensure_same_boundary(parent, metadata.identity)
    return metadata


def atomic_rename_no_replace(
    source_parent: PinnedDirectory,
    source_name: str,
    destination_parent: PinnedDirectory,
    destination_name: str,
    *,
    expected_identity: FileIdentity,
    directory: bool,
) -> None:
    """Rename through pinned parents atomically without replacing a destination."""

    _validate_child_name(source_name)
    _validate_child_name(destination_name)
    actual_identity = child_identity(source_parent, source_name, directory=directory)
    if actual_identity != expected_identity:
        raise IdentityChangedError("The rename source changed identity before publication.")
    if source_parent.identity.device != destination_parent.identity.device:
        raise UnsupportedFilesystemError("Atomic publication across filesystems is not supported.")
    if (
        source_parent.identity.mount_id is not None
        and destination_parent.identity.mount_id is not None
        and source_parent.identity.mount_id != destination_parent.identity.mount_id
    ):
        raise UnsupportedFilesystemError("Atomic publication across Linux mounts is not supported.")
    invoke_test_hook(
        "before_rename",
        source_parent=source_parent,
        source_name=source_name,
        destination_parent=destination_parent,
        destination_name=destination_name,
        directory=directory,
    )
    if child_exists(destination_parent, destination_name):
        raise DestinationExistsError("The exclusive rename destination already exists.")

    if os.name == "nt":
        try:
            source_handle = _windows_open_relative(
                source_parent.handle,
                source_name,
                create=False,
                directory=directory,
                delete_access=True,
            )
        except OSError as exc:
            raise FilesystemSafetyError(
                "The Windows rename source could not be opened through its pinned parent."
            ) from exc
        try:
            if _windows_identity(source_handle) != expected_identity:
                raise IdentityChangedError("The rename source changed identity before publication.")
            try:
                _windows_rename_handle(
                    source_handle,
                    destination_parent.handle,
                    destination_name,
                )
            except OSError as exc:
                if child_exists(destination_parent, destination_name):
                    raise DestinationExistsError(
                        "The exclusive rename destination appeared during publication."
                    ) from exc
                raise FilesystemSafetyError("The Windows handle-relative rename failed.") from exc
        finally:
            _kernel32.CloseHandle(source_handle)
    elif sys.platform.startswith("linux"):
        library = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(library, "renameat2", None)
        if renameat2 is None:
            raise UnsupportedFilesystemError("Linux renameat2 is unavailable; publication was blocked.")
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        result = renameat2(
            source_parent.handle,
            os.fsencode(source_name),
            destination_parent.handle,
            os.fsencode(destination_name),
            1,  # RENAME_NOREPLACE
        )
        if result != 0:
            error_number = ctypes.get_errno()
            if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
                raise DestinationExistsError("The exclusive rename destination appeared.")
            if error_number in {errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EINVAL}:
                raise UnsupportedFilesystemError(
                    "This Linux filesystem lacks the required renameat2 no-replace support."
                )
            raise FilesystemSafetyError(
                f"Linux handle-relative renameat2 failed with OS error {error_number}."
            )
    elif sys.platform == "darwin":
        library = ctypes.CDLL(None, use_errno=True)
        renameatx_np = getattr(library, "renameatx_np", None)
        if renameatx_np is None:
            raise UnsupportedFilesystemError(
                "macOS renameatx_np is unavailable; publication was blocked."
            )
        renameatx_np.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameatx_np.restype = ctypes.c_int
        result = renameatx_np(
            source_parent.handle,
            os.fsencode(source_name),
            destination_parent.handle,
            os.fsencode(destination_name),
            0x00000004,  # RENAME_EXCL
        )
        if result != 0:
            error_number = ctypes.get_errno()
            if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
                raise DestinationExistsError("The exclusive rename destination appeared.")
            if error_number in {errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EINVAL}:
                raise UnsupportedFilesystemError(
                    "This macOS filesystem lacks exclusive renameatx_np support."
                )
            raise FilesystemSafetyError(
                f"macOS handle-relative renameatx_np failed with OS error {error_number}."
            )
    else:
        raise UnsupportedFilesystemError(
            "This platform lacks a supported handle-relative no-replace rename primitive."
        )
    invoke_test_hook(
        "after_rename",
        source_parent=source_parent,
        source_name=source_name,
        destination_parent=destination_parent,
        destination_name=destination_name,
        directory=directory,
    )


def write_file_exclusive(parent: PinnedDirectory, name: str, data: bytes) -> FileIdentity:
    """Create and flush one new regular file through a pinned parent."""

    _validate_child_name(name)
    if os.name == "nt":
        try:
            handle = _windows_open_relative(
                parent.handle,
                name,
                create=True,
                directory=False,
                delete_access=True,
                write_access=True,
            )
        except DestinationExistsError:
            raise
        except OSError as exc:
            raise FilesystemSafetyError(f"File could not be created safely: {name}") from exc
        try:
            _windows_write_all(handle, data)
            identity = _windows_identity(handle)
        except Exception as exc:
            try:
                _windows_mark_delete(handle)
            finally:
                _kernel32.CloseHandle(handle)
            if isinstance(exc, OSError):
                raise FilesystemSafetyError(f"File could not be written safely: {name}") from exc
            raise
        else:
            _kernel32.CloseHandle(handle)
            return identity
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, 0o600, dir_fd=parent.handle)
    except FileExistsError as exc:
        raise DestinationExistsError(f"File already exists: {name}") from exc
    except OSError as exc:
        raise FilesystemSafetyError(f"File could not be created safely: {name}") from exc
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written == 0:
                raise FilesystemSafetyError("The operating system reported a zero-length file write.")
            view = view[written:]
        os.fsync(descriptor)
        return _posix_identity(descriptor)
    except Exception:
        os.close(descriptor)
        descriptor = -1
        raise FilesystemSafetyError(
            f"File write failed; the partial path was left for manual inspection: {name}"
        )
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def read_file(
    parent: PinnedDirectory,
    name: str,
    *,
    expected_identity: FileIdentity | None = None,
    max_bytes: int | None = None,
) -> tuple[bytes, FileIdentity]:
    """Read one verified regular file through a pinned parent."""

    _validate_child_name(name)
    if parent._closed:
        raise FilesystemSafetyError("A closed directory capability cannot be used for reading.")
    if max_bytes is not None and max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer when supplied.")
    invoke_test_hook(
        "before_file_read",
        parent=parent,
        name=name,
        expected_identity=expected_identity,
    )
    if os.name == "nt":
        try:
            handle = _windows_open_relative(
                parent.handle,
                name,
                create=False,
                directory=False,
            )
        except OSError as exc:
            raise FilesystemSafetyError(f"File could not be opened safely: {name}") from exc
        try:
            identity = _windows_identity(handle)
            information = _windows_information(handle)
            if (
                information.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT
                or information.dwFileAttributes & stat.FILE_ATTRIBUTE_DIRECTORY
                or information.nNumberOfLinks != 1
            ):
                raise FilesystemSafetyError("Expected a single-link regular file.")
            _ensure_same_boundary(parent, identity)
            if expected_identity is not None and identity != expected_identity:
                raise IdentityChangedError("File identity changed before it was read.")
            size = (int(information.nFileSizeHigh) << 32) | int(information.nFileSizeLow)
            if max_bytes is not None and size > max_bytes:
                raise FilesystemSafetyError("File exceeds the configured size limit.")
            invoke_test_hook(
                "file_read_opened",
                parent=parent,
                name=name,
                identity=identity,
            )
            data = _windows_read_all(handle, max_bytes=max_bytes)
            final_information = _windows_information(handle)
            final_identity = _windows_identity(handle)
            if (
                final_identity != identity
                or final_information.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT
                or final_information.dwFileAttributes & stat.FILE_ATTRIBUTE_DIRECTORY
                or final_information.nNumberOfLinks != 1
            ):
                raise IdentityChangedError("File identity changed while it was read.")
            final_size = (
                (int(final_information.nFileSizeHigh) << 32)
                | int(final_information.nFileSizeLow)
            )
            initial_write_time = (
                int(information.ftLastWriteTime.dwHighDateTime),
                int(information.ftLastWriteTime.dwLowDateTime),
            )
            final_write_time = (
                int(final_information.ftLastWriteTime.dwHighDateTime),
                int(final_information.ftLastWriteTime.dwLowDateTime),
            )
            if final_size != size or final_write_time != initial_write_time:
                raise IdentityChangedError("File metadata changed while it was read.")
            if max_bytes is not None and final_size > max_bytes:
                raise FilesystemSafetyError("File exceeded the configured size limit while reading.")
        except OSError as exc:
            raise FilesystemSafetyError(f"File could not be read safely: {name}") from exc
        finally:
            _kernel32.CloseHandle(handle)
    else:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(name, flags, dir_fd=parent.handle)
        except OSError as exc:
            raise FilesystemSafetyError(f"File could not be opened safely: {name}") from exc
        try:
            observation = os.fstat(descriptor)
            if (
                not stat.S_ISREG(observation.st_mode)
                or _is_reparse(observation)
                or observation.st_nlink != 1
            ):
                raise FilesystemSafetyError("Expected a single-link regular file.")
            identity = _posix_identity(descriptor)
            _ensure_same_boundary(parent, identity)
            if expected_identity is not None and identity != expected_identity:
                raise IdentityChangedError("File identity changed before it was read.")
            if max_bytes is not None and observation.st_size > max_bytes:
                raise FilesystemSafetyError("File exceeds the configured size limit.")
            invoke_test_hook(
                "file_read_opened",
                parent=parent,
                name=name,
                identity=identity,
            )
            chunks: list[bytes] = []
            total = 0
            while True:
                read_size = 1024 * 1024
                if max_bytes is not None:
                    read_size = min(read_size, max_bytes + 1 - total)
                    if read_size <= 0:
                        raise FilesystemSafetyError(
                            "File exceeded the configured size limit while reading."
                        )
                block = os.read(descriptor, read_size)
                if not block:
                    break
                chunks.append(block)
                total += len(block)
                if max_bytes is not None and total > max_bytes:
                    raise FilesystemSafetyError(
                        "File exceeded the configured size limit while reading."
                    )
            final_observation = os.fstat(descriptor)
            if (
                not stat.S_ISREG(final_observation.st_mode)
                or _is_reparse(final_observation)
                or final_observation.st_nlink != 1
                or _posix_identity(descriptor) != identity
            ):
                raise IdentityChangedError("File identity changed while it was read.")
            if (
                final_observation.st_size != observation.st_size
                or final_observation.st_mtime_ns != observation.st_mtime_ns
                or final_observation.st_ctime_ns != observation.st_ctime_ns
            ):
                raise IdentityChangedError("File metadata changed while it was read.")
            if max_bytes is not None and final_observation.st_size > max_bytes:
                raise FilesystemSafetyError("File exceeded the configured size limit while reading.")
            data = b"".join(chunks)
        except OSError as exc:
            raise FilesystemSafetyError(f"File could not be read safely: {name}") from exc
        finally:
            os.close(descriptor)

    if child_identity(parent, name, directory=False) != identity:
        raise IdentityChangedError("File name changed identity while it was read.")
    return data, identity


def read_utf8_file(
    parent: PinnedDirectory,
    name: str,
    *,
    max_bytes: int,
    expected_identity: FileIdentity | None = None,
) -> tuple[str, FileIdentity]:
    """Read bounded UTF-8 input once through a non-following directory capability."""

    data, identity = read_file(
        parent,
        name,
        expected_identity=expected_identity,
        max_bytes=max_bytes,
    )
    try:
        return data.decode("utf-8"), identity
    except UnicodeDecodeError as exc:
        raise FilesystemSafetyError(f"File is not valid UTF-8 text: {name}") from exc


def remove_file(
    parent: PinnedDirectory,
    name: str,
    *,
    expected_identity: FileIdentity,
    expected_content: bytes,
) -> None:
    """Remove a known temporary file without deleting a raced replacement."""

    _validate_child_name(name)
    try:
        actual, identity = read_file(
            parent,
            name,
            expected_identity=expected_identity,
            max_bytes=max(1, len(expected_content)),
        )
    except FilesystemSafetyError as exc:
        raise IdentityChangedError(
            f"Cleanup ownership is ambiguous; leave this path for inspection: {name}"
        ) from exc
    if identity != expected_identity or actual != expected_content:
        raise IdentityChangedError(
            f"Cleanup content changed; leave this path for inspection: {name}"
        )

    invoke_test_hook(
        "before_remove_file",
        parent=parent,
        name=name,
        expected_identity=expected_identity,
    )
    quarantine_name = f".osito-cleanup-{secrets.token_hex(12)}.tmp"
    try:
        atomic_rename_no_replace(
            parent,
            name,
            parent,
            quarantine_name,
            expected_identity=expected_identity,
            directory=False,
        )
    except Exception as exc:
        raise IdentityChangedError(
            "Cleanup could not isolate the expected file; leave any entry at "
            f"{name} or {quarantine_name} for manual inspection."
        ) from exc

    try:
        quarantined, quarantined_identity = read_file(
            parent,
            quarantine_name,
            expected_identity=expected_identity,
            max_bytes=max(1, len(expected_content)),
        )
        verified = (
            quarantined_identity == expected_identity
            and quarantined == expected_content
        )
    except FilesystemSafetyError:
        verified = False

    if not verified:
        try:
            metadata = inspect_child(parent, quarantine_name)
            if child_exists(parent, name):
                raise IdentityChangedError(
                    f"Both {name} and {quarantine_name} require manual inspection."
                )
            atomic_rename_no_replace(
                parent,
                quarantine_name,
                parent,
                name,
                expected_identity=metadata.identity,
                directory=metadata.kind == "directory",
            )
        except Exception as exc:
            raise IdentityChangedError(
                f"A replacement was preserved at {quarantine_name}; inspect it manually."
            ) from exc
        raise IdentityChangedError(
            f"A replacement was preserved at {name}; cleanup was not performed. "
            "Inspect it manually."
        )

    try:
        if os.name == "nt":
            handle = _windows_open_relative(
                parent.handle,
                quarantine_name,
                create=False,
                directory=False,
                delete_access=True,
            )
            try:
                if _windows_identity(handle) != expected_identity:
                    raise IdentityChangedError(
                        f"Cleanup quarantine changed; inspect {quarantine_name}."
                    )
                if (
                    _windows_read_all(
                        handle,
                        max_bytes=max(1, len(expected_content)),
                    )
                    != expected_content
                ):
                    raise IdentityChangedError(
                        f"Cleanup quarantine content changed; inspect {quarantine_name}."
                    )
                _windows_mark_delete(handle)
            finally:
                _kernel32.CloseHandle(handle)
        else:
            # POSIX has no portable conditional-unlink primitive. The random
            # quarantine name is isolated and fully revalidated immediately
            # above; continuously racing that private name is outside v0.1's
            # trusted-workspace threat model.
            os.unlink(quarantine_name, dir_fd=parent.handle)
    except Exception as exc:
        raise IdentityChangedError(
            f"Verified temporary file could not be removed; inspect {quarantine_name}."
        ) from exc


def remove_empty_directory(
    parent: PinnedDirectory,
    name: str,
    *,
    expected_identity: FileIdentity,
) -> None:
    """Remove a known empty temporary directory conservatively."""

    _validate_child_name(name)
    child = open_child_directory(parent, name)
    try:
        if child.identity != expected_identity or list_child_names(child):
            raise IdentityChangedError(
                f"Cleanup directory changed; leave this path for inspection: {name}"
            )
    finally:
        child.close()

    invoke_test_hook(
        "before_remove_empty_directory",
        parent=parent,
        name=name,
        expected_identity=expected_identity,
    )
    quarantine_name = f".osito-cleanup-{secrets.token_hex(12)}.dir"
    try:
        atomic_rename_no_replace(
            parent,
            name,
            parent,
            quarantine_name,
            expected_identity=expected_identity,
            directory=True,
        )
    except Exception as exc:
        raise IdentityChangedError(
            "Cleanup could not isolate the expected directory; leave any entry at "
            f"{name} or {quarantine_name} for manual inspection."
        ) from exc

    verified = False
    try:
        quarantined = open_child_directory(parent, quarantine_name)
        try:
            verified = (
                quarantined.identity == expected_identity
                and not list_child_names(quarantined)
            )
        finally:
            quarantined.close()
    except FilesystemSafetyError:
        verified = False

    if not verified:
        try:
            metadata = inspect_child(parent, quarantine_name)
            if child_exists(parent, name):
                raise IdentityChangedError(
                    f"Both {name} and {quarantine_name} require manual inspection."
                )
            atomic_rename_no_replace(
                parent,
                quarantine_name,
                parent,
                name,
                expected_identity=metadata.identity,
                directory=metadata.kind == "directory",
            )
        except Exception as exc:
            raise IdentityChangedError(
                f"A replacement directory was preserved at {quarantine_name}; inspect it manually."
            ) from exc
        raise IdentityChangedError(
            f"A replacement directory was preserved at {name}; cleanup was not performed. "
            "Inspect it manually."
        )

    try:
        if os.name == "nt":
            handle = _windows_open_relative(
                parent.handle,
                quarantine_name,
                create=False,
                directory=True,
                delete_access=True,
            )
            try:
                if _windows_identity(handle) != expected_identity:
                    raise IdentityChangedError(
                        f"Cleanup quarantine changed; inspect {quarantine_name}."
                    )
                if _windows_list_names(handle):
                    raise IdentityChangedError(
                        f"Cleanup quarantine is no longer empty; inspect {quarantine_name}."
                    )
                _windows_mark_delete(handle)
            finally:
                _kernel32.CloseHandle(handle)
        else:
            # See remove_file: deletion follows isolation under an unpredictable
            # name and immediate revalidation. A hostile process racing that
            # private name is outside the practical v0.1 threat model.
            os.rmdir(quarantine_name, dir_fd=parent.handle)
    except Exception as exc:
        raise IdentityChangedError(
            f"Verified temporary directory could not be removed; inspect {quarantine_name}."
        ) from exc


def publish_text_exclusive(
    parent: PinnedDirectory,
    name: str,
    text: str,
) -> FileIdentity:
    """Publish UTF-8 text atomically without replacing an existing child."""

    _validate_child_name(name)
    temporary_name = f".osito-publish-{secrets.token_hex(12)}.tmp"
    expected_bytes = text.encode("utf-8")
    temporary_identity = write_file_exclusive(parent, temporary_name, expected_bytes)
    completed = False
    try:
        atomic_rename_no_replace(
            parent,
            temporary_name,
            parent,
            name,
            expected_identity=temporary_identity,
            directory=False,
        )
        published_identity = child_identity(parent, name, directory=False)
        if published_identity != temporary_identity:
            raise IdentityChangedError("Published file identity did not match the prepared file.")
        actual, verified_identity = read_file(parent, name)
        if verified_identity != temporary_identity or actual != text.encode("utf-8"):
            raise IdentityChangedError("Published file content or identity verification failed.")
        completed = True
        return temporary_identity
    finally:
        if not completed:
            if child_exists(parent, temporary_name):
                remove_file(
                    parent,
                    temporary_name,
                    expected_identity=temporary_identity,
                    expected_content=expected_bytes,
                )
            else:
                raise PublicationOutcomeError(
                    "Publication outcome is ambiguous; the final path was left untouched for "
                    f"manual inspection: {name}"
                )
