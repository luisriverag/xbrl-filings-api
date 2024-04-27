"""Define class `DownloadSpecs`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Optional, Union

__all__ = ['DownloadSpecs']


@dataclass(frozen=True)
class DownloadSpecs:
    """
    Dataclass of parameter values for ``downloader.download_async()``.

    Used as download instructions in lists for parallel download
    functions which eventually end up as parameters for
    :func:`download_async()`. Attribute `info` is only for keeping track
    of downloads and is not used as a function parameter.
    """

    url: str
    """URL to download."""

    to_dir: Union[str, PurePath]
    """Directory to save the downloaded file."""

    stem_pattern: Optional[str] = None
    """
    Pattern to add to the filename stems.

    Placeholder ``"/name/"`` is always required.
    """

    filename: Optional[str] = None
    """Name to be used for the saved file."""

    sha256: Optional[str] = None
    """
    Expected SHA-256 checksum as a hex string.

    Case-insensitive. No checksum is calculated if this parameter is not
    given.
    """

    info: Any = None
    """Download-specific information."""
