"""Common constants for the library."""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime

# Exclude attributes with Python objects and lists of objects in
# subclasses of `APIResource` to not end up in the data outputs.
ATTRS_ALWAYS_EXCLUDE_FROM_DATA = {
    'type',
    'entity',
    'validation_messages',
    'filings',
    'filing'
    }

ResourceLiteralType = str | int | datetime | date
YearFilterMonthsType = tuple[tuple[int, int], tuple[int, int]]
