"""Define class `DownloadResult`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DownloadResult:
    """Result object from finished downloads."""

    url: str
    """URL which was downloaded or attempted to download."""

    path: str | None = None
    """Path where the downloaded file was saved."""

    err: Exception | None = None
    """Exception raised while the file was being downloaded."""

    obj: Any = None
    """Reference object related to this download."""

    file: str | None = None
    """File format of the downloaded file."""
