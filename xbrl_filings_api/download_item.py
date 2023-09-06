"""Define `DownloadItem` dataclass."""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import PurePath
from typing import Optional


@dataclass
class DownloadItem:
    """
    Download item class for `xbrl_filings_api`.

    Will be internally parsed into a `DownloadSpecs` object based on
    caller method arguments.
    """

    filename: Optional[str] = None
    to_dir: Optional[str | PurePath] = None
    stem_pattern: Optional[str] = None
