"""Common constants for the library."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime
from typing import Literal, Union

NO_LIMIT = 0
"""
Fetches all filings that match the query.

Used as a value to the `limit` parameter
"""

ATTRS_ALWAYS_EXCLUDE_FROM_DATA = {
    'type',
    'entity',
    'validation_messages',
    'filings',
    'filing'
    }
"""
Exclude non-data attributes from `APIResource` data columns.

Exclude attributes whose value is a functional object or some sort of
list from the data output.
"""

class _Prototype:
    """Type of special value `_PROTOTYPE`."""

_PROTOTYPE = _Prototype()
"""A special value for APIResource to construct a dummy instance."""

DataAttributeType = Union[str, int, datetime, date, None]
"""Type of `APIResource` data attribute."""

YearFilterMonthsType = tuple[tuple[int, int], tuple[int, int]]
"""Months chosen when only a year is given in a date filter."""

FileStringType = Literal['json', 'package', 'xhtml']
"""String used in `files` parameter and `DownloadInfo.file`."""
