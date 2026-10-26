import os
import shutil
import tempfile
import threading
from typing import Set

_tracked_paths: Set[str] = set()
_lock = threading.Lock()


def register_temp_path(path: str) -> None:
    """Register a file or directory path to be cleaned up later."""
    if path:
        with _lock:
            _tracked_paths.add(os.path.abspath(path))


def create_temp_dir() -> str:
    """Create a temporary directory and register it for cleanup."""
    temp_dir = tempfile.mkdtemp(prefix="media_dl_")
    register_temp_path(temp_dir)
    return temp_dir


def cleanup() -> None:
    """Delete all registered temporary files and directories."""
    with _lock:
        paths = list(_tracked_paths)
        _tracked_paths.clear()

    for path in paths:
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
