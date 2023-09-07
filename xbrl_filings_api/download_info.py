"""Define `DownloadInfo` dataclass."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any


@dataclass(kw_only=True)
class DownloadInfo:
    """Download info class for `DownloadItem` objects."""

    obj: Any
    """Filing object which is used as the origin for the download."""
    file: str
    """
    File type to download.

    Used as an attribute prefix while assigning save paths to `obj`.
    """
