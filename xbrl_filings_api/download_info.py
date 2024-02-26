"""Define `DownloadInfo` dataclass."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class DownloadInfo:
    """Attribute `info` for `DownloadSpecs` objects."""

    obj: Any
    """Filing object which is used as the origin for the download."""

    file: Literal['json', 'package', 'xhtml']
    """
    File type to download.

    Used as an attribute prefix while assigning save paths to `obj`.
    """
