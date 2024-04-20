"""Define `DownloadInfo` dataclass."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any

from xbrl_filings_api.constants import FileStringType

__all__ = ['DownloadInfo']


@dataclass
class DownloadInfo:
    """Dataclass for attribute `DownloadSpecs.info`."""

    obj: Any
    """Filing object which is used as the origin for the download."""

    file: FileStringType
    """
    File type to download.

    Used as an attribute prefix while assigning save paths to `obj`.
    """
