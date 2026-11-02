"""Checksum calculation (MD5 / SHA1) with progress reporting.

Runs in chunks so the caller can report progress and cancel between chunks.
"""

from __future__ import annotations

import hashlib
import os
from typing import Callable

CHUNK_SIZE = 1024 * 1024  # 1 MiB

SUPPORTED_ALGORITHMS = ("md5", "sha1")


class ChecksumError(Exception):
    """Raised when a checksum cannot be calculated."""


def compute_checksum(
    path: str,
    algorithm: str = "md5",
    chunk_size: int = CHUNK_SIZE,
    progress: Callable[[int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> str:
    """Return the hex digest of *path* using *algorithm* (md5 or sha1).

    *progress* receives the percentage (0-100).  *should_cancel* is checked
    between chunks; when it returns True the calculation stops and
    :class:`ChecksumError` is raised.
    """
    algorithm = algorithm.lower()
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ChecksumError("Unsupported checksum algorithm: %s" % algorithm)
    if not os.path.isfile(path):
        raise ChecksumError("Not a readable file: %s" % path)

    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ChecksumError(str(exc)) from exc

    total_size = os.path.getsize(path)
    bytes_read = 0

    with open(path, "rb") as handle:
        while True:
            if should_cancel is not None and should_cancel():
                raise ChecksumError("cancelled")
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
            bytes_read += len(chunk)
            if progress is not None:
                if total_size:
                    progress(min(100, int(bytes_read * 100 / total_size)))
                else:
                    progress(100)

    if progress is not None:
        progress(100)
    return digest.hexdigest()
