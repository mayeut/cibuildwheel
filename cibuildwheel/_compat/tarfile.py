# Based on https://github.com/pypa/build/blob/f4ebd495cc0c2c74155bd4fe48b76399fb7927ac/src/build/_compat/tarfile.py

from __future__ import annotations

import sys
import tarfile

TYPE_CHECKING = False
if TYPE_CHECKING:
    from pathlib import Path

    TarFile = tarfile.TarFile

# Per https://peps.python.org/pep-0706/, the "data" filter will become
# the default in Python 3.14. The first series of releases with the filter
# had a broken filter that could not process symlinks correctly.
elif sys.version_info < (3, 14):

    class TarFile(tarfile.TarFile):  # pragma: no cover
        extraction_filter = staticmethod(tarfile.data_filter)

else:
    TarFile = tarfile.TarFile  # pragma: no cover


def safe_extractall(tar: tarfile.TarFile, path: Path) -> None:  # pragma: no cover
    """Extract every member of ``tar`` into ``path`` via the PEP 706 ``data`` filter."""
    tar.extractall(path, filter="data")


__all__ = [
    "TarFile",
    "safe_extractall",
]
