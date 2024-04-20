"""Define `DownloadItem` dataclass."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import PurePath
from typing import Optional, Union

__all__ = ['DownloadItem']


@dataclass
class DownloadItem:
    """
    Dataclass defining download item for download functions.

    Attributes override download function parameters values for
    downloads of this file (JSON, XHTML, or package).
    """

    filename: Optional[str] = None
    """
    Name to be used for the saved file.

    Can only be set for `Filing` object download methods.
    """

    to_dir: Optional[Union[str, PurePath]] = None
    """Directory to save the file."""

    stem_pattern: Optional[str] = None
    """
    Pattern to add to the filename stems.

    Placeholder "/name/" is always required.
    """
