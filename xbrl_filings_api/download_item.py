"""Define `DownloadItem` dataclass."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import PurePath
from typing import Optional


@dataclass
class DownloadItem:
    """
    Download item class for download functions.

    Can be used to override download function parameters for a single
    file.
    """

    filename: Optional[str] = None
    """Name to be used for the saved file."""

    to_dir: Optional[str | PurePath] = None
    """Directory to save the file."""

    stem_pattern: Optional[str] = None
    """
    Pattern to add to the filename stems.

    Placeholder ``/name/`` is always required.
    """
