"""Define class `DownloadResult`."""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DownloadResult:
    """Result object from finished downloads."""

    obj: Any
    file: str
    path: str | None = None
    err: Exception | None = None
