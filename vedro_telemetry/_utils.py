from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path
from time import time
from typing import Optional, Union

__all__ = ("now", "get_project_name", "get_package_version",)


def _get_project_name(path: Path) -> Union[str, None]:
    """
    Recursively retrieve the name of the project by looking for a `.git` directory.

    This function searches up the directory tree from the specified path for a `.git`
    folder to determine if the path is part of a Git project. If a `.git` directory
    is found, the function returns the name of the directory, which is assumed to be
    the project name.

    :param path: The starting path to search for a `.git` folder.
    :return: The name of the project directory if found, otherwise `None`.
    """
    maybe_git = path / ".git"
    if maybe_git.exists() and maybe_git.is_dir():
        return path.name

    if path == Path(path.root):
        return None

    return _get_project_name(path.parent)


def get_project_name(path: Optional[Path] = None, *, default: str = "") -> str:
    """
    Retrieve the name of the project based on the presence of a `.git` directory.

    This function tries to determine the project name by looking for a `.git` folder
    in the specified or current directory. If no `.git` folder is found, the function
    returns a default value.

    :param path: The starting directory path to search. If not provided, the current
                 working directory is used.
    :param default: The default project name to return if no project is found. Default
                    is an empty string.
    :return: The project name if found, otherwise the specified default value.
    """
    if path is None:
        path = Path()

    if not path.is_absolute():
        path = path.absolute()

    if project_name := _get_project_name(path):
        return project_name
    return default


def get_package_version(name: str, *, default: str = "0.0.0") -> str:
    """
    Retrieve the version of the installed package with the specified name.

    This function queries the installed package metadata to get the version number.
    If the package is not found, a default version string is returned.

    :param name: The name of the package to retrieve the version for.
    :param default: The default version string to return if the package is not found.
                    Default is "0.0.0".
    :return: The version string of the package if found, otherwise the specified default value.
    """
    try:
        version = metadata(name)
    except PackageNotFoundError:
        return default
    return str(version["Version"]) if ("Version" in version) else default


def now() -> int:
    """
    Get the current time in milliseconds since the Unix epoch.

    This function returns the current time as an integer, representing the number
    of milliseconds since January 1, 1970 (Unix epoch).

    :return: The current time in milliseconds.
    """
    return round(time() * 1000)
