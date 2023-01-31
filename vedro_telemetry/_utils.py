from pathlib import Path
from typing import Optional, Union

__all__ = ("get_project_name",)


def _get_project_name(path: Path) -> Union[str, None]:
    maybe_git = path / ".git"
    if maybe_git.exists() and maybe_git.is_dir():
        return path.name

    if path == Path(path.root):
        return None

    return _get_project_name(path.parent)


def get_project_name(path: Optional[Path] = None) -> Union[str, None]:
    if path is None:
        path = Path()

    if not path.is_absolute():
        path = path.absolute()

    return _get_project_name(path)
