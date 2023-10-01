"""Common constants for the library."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime
from typing import Union

NO_LIMIT = 0
"""."""

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

ResourceLiteralType = Union[str, int, datetime, date]
"""Concrete datatype of `APIResource` data attribute."""

YearFilterMonthsType = tuple[tuple[int, int], tuple[int, int]]
"""Months chosen when only a year is given in a date filter."""
