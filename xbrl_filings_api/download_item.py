# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Optional


@dataclass(frozen=True)
class FullDownloadItem:
    url: str
    to_dir: str | PurePath
    obj: Any
    attr_base: Optional[str] = None
    stem_pattern: Optional[str] = None
    filename: Optional[str] = None
    sha256: Optional[str] = None


@dataclass
class DownloadItem:
    filename: Optional[str] = None
    to_dir: Optional[str | PurePath] = None
    stem_pattern: Optional[str] = None
