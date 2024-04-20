"""Define class `DownloadResult`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Union

__all__ = ['DownloadResult']


@dataclass(frozen=True)
class DownloadResult:
    """Dataclass for result information from a finished download."""

    url: str
    """URL which was downloaded or attempted to download."""

    path: Union[str, None] = None
    """Path where the downloaded file was saved."""

    err: Union[Exception, None] = None
    """Exception raised while the file was being downloaded."""

    info: Any = None
    """Value of `DownloadSpecs.info` for parallel downloads."""
