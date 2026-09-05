# Based on https://github.com/pypa/build/blob/f4ebd495cc0c2c74155bd4fe48b76399fb7927ac/src/build/_compat/tarfile.py

from __future__ import annotations

import tarfile

TYPE_CHECKING = False
if TYPE_CHECKING:
    from pathlib import Path

TarFile = tarfile.TarFile  # pragma: no cover


def safe_extractall(tar: tarfile.TarFile, path: Path) -> None:  # pragma: no cover
    """Extract every member of ``tar`` into ``path`` via the PEP 706 ``data`` filter."""
    tar.extractall(path, filter="data")


__all__ = [
    "TarFile",
    "safe_extractall",
]
