from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path
from time import time
from typing import Optional, Union

__all__ = ("now", "get_project_name", "get_package_version",)


def _get_project_name(path: Path) -> Union[str, None]:
    maybe_git = path / ".git"
    if maybe_git.exists() and maybe_git.is_dir():
        return path.name

    if path == Path(path.root):
        return None

    return _get_project_name(path.parent)


def get_project_name(path: Optional[Path] = None, *, default: str = "") -> str:
    if path is None:
        path = Path()

    if not path.is_absolute():
        path = path.absolute()

    if project_name := _get_project_name(path):
        return project_name
    return default


def get_package_version(name: str, *, default: str = "0.0.0") -> str:
    try:
        version = metadata(name)
    except PackageNotFoundError:
        return default
    return str(version["Version"]) if ("Version" in version) else default


def now() -> int:
    return round(time() * 1000)
