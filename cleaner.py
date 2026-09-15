from __future__ import annotations

import os
import platform
import shutil
import stat
import time
from dataclasses import dataclass, field
from pathlib import Path

IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

try:
    from send2trash import send2trash

    HAS_TRASH = True
except Exception:
    HAS_TRASH = False

DAY = 86400.0
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", ".localized"}
JUNK_PREFIXES = ("~$", ".~")
JUNK_SUFFIXES = (".tmp", ".temp", ".crdownload", ".download", ".part", ".partial", ".log1")


@dataclass
class FileItem:
    path: Path
    size: int

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class ScanResult:
    key: str
    title: str
    items: list[FileItem] = field(default_factory=list)
    note: str = ""
    permanent_only: bool = False

    @property
    def total_size(self) -> int:
        return sum(item.size for item in self.items)

    @property
    def count(self) -> int:
        return len(self.items)


def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _is_link(path: Path) -> bool:
    try:
        return path.is_symlink()
    except OSError:
        return True


def _walk_files(root: Path, min_age: float = 0.0, max_entries: int = 4000):
    now = time.time()
    found = 0
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if not _is_link(Path(dirpath) / d)]
        for name in filenames:
            if found >= max_entries:
                return
            path = Path(dirpath) / name
            if _is_link(path):
                continue
            try:
                st = path.stat()
            except OSError:
                continue
            if not stat.S_ISREG(st.st_mode):
                continue
            if min_age and (now - st.st_mtime) < min_age:
                continue
            yield FileItem(path, st.st_size)
            found += 1


def _root_candidates():
    home = Path.home()
    if IS_WIN:
        return {
            "temp": [
                Path(os.environ.get("TEMP", home / "AppData/Local/Temp")),
                Path(os.environ.get("TMP", home / "AppData/Local/Temp")),
            ],
            "cache": [
                Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")) / "Temp",
                Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")) / "Microsoft/Windows/INetCache",
            ],
            "trash": [],
        }
    return {
        "temp": [Path("/tmp"), Path("/var/tmp")],
        "cache": [home / "Library/Caches"],
        "trash": [home / ".Trash"],
    }


def scan_temp() -> ScanResult:
    result = ScanResult("temp", "临时文件")
    seen = set()
    for root in _root_candidates()["temp"]:
        if not root or str(root) in seen:
            continue
        seen.add(str(root))
        for item in _walk_files(root, min_age=DAY):
            result.items.append(item)
    result.note = "只列出 1 天前修改、且不是软链接的普通文件。"
    return result


def scan_cache() -> ScanResult:
    result = ScanResult("cache", "应用缓存")
    seen = set()
    for root in _root_candidates()["cache"]:
        if not root or str(root) in seen:
            continue
        seen.add(str(root))
        for item in _walk_files(root, min_age=DAY):
            result.items.append(item)
    result.note = "缓存可安全删除，但部分应用首次打开会稍慢。"
    return result


def scan_downloads() -> ScanResult:
    result = ScanResult("downloads", "下载文件夹")
    root = Path.home() / "Downloads"
    for item in _walk_files(root, min_age=0, max_entries=3000):
        result.items.append(item)
    result.items.sort(key=lambda i: i.size, reverse=True)
    result.note = "默认全部不勾选，请自行选择要删除的文件。"
    return result


def scan_desktop_junk() -> ScanResult:
    result = ScanResult("desktop", "桌面无用文件")
    root = Path.home() / "Desktop"
    if not root.exists():
        root = Path.home() / "桌面"
    for item in _walk_files(root, min_age=0, max_entries=2000):
        name = item.name
        if (
            name in JUNK_NAMES
            or name.startswith(JUNK_PREFIXES)
            or name.lower().endswith(JUNK_SUFFIXES)
        ):
            result.items.append(item)
    result.note = "只匹配系统垃圾与临时文件（.DS_Store、Thumbs.db、~$ 等）。"
    return result


def scan_trash() -> ScanResult:
    result = ScanResult("trash", "回收站 / 废纸篓")
    if IS_WIN:
        result.permanent_only = True
        result.note = "Windows 回收站将直接清空（不可恢复）。"
        return result
    root = Path.home() / ".Trash"
    for item in _walk_files(root, min_age=0, max_entries=5000):
        result.items.append(item)
    result.note = "清空后文件将无法恢复。"
    result.permanent_only = True
    return result


def trash_size() -> tuple[int, int]:
    if IS_WIN:
        return (0, 0)
    root = Path.home() / ".Trash"
    total = 0
    count = 0
    for item in _walk_files(root, min_age=0, max_entries=20000):
        total += item.size
        count += 1
    return (count, total)


def empty_recycle_bin() -> tuple[bool, str]:
    if not IS_WIN:
        return (False, "仅 Windows 支持")
    try:
        import ctypes

        result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000001 | 0x00000002 | 0x00000004)
        if result == 0:
            return (True, "回收站已清空")
        return (False, f"清空失败，错误码 {result}")
    except Exception as exc:
        return (False, str(exc))


def delete_items(items: list[FileItem], permanent: bool = False):
    deleted = 0
    freed = 0
    errors: list[tuple[Path, str]] = []
    for item in items:
        try:
            if permanent or not HAS_TRASH:
                item.path.unlink()
            else:
                send2trash(str(item.path))
            deleted += 1
            freed += item.size
        except Exception as exc:
            errors.append((item.path, str(exc)))
    return deleted, freed, errors


def disk_usage():
    home = Path.home()
    try:
        usage = shutil.disk_usage(str(home))
    except OSError:
        usage = shutil.disk_usage(str(Path.home().anchor))
    return usage


def top_space_dirs(limit: int = 8):
    home = Path.home()
    results = []
    if not home.exists():
        return results
    try:
        for child in home.iterdir():
            if not child.is_dir() or _is_link(child):
                continue
            size = 0
            for dirpath, dirnames, filenames in os.walk(child, followlinks=False):
                dirnames[:] = [d for d in dirnames if not _is_link(Path(dirpath) / d)]
                for name in filenames:
                    size += _file_size(Path(dirpath) / name)
            results.append((child.name, size))
    except OSError:
        pass
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]
