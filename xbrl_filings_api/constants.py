"""Common constants for the library."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime
from typing import Literal, Union

__all__ = [
    'api_attribute_map',
    'ATTRS_ALWAYS_EXCLUDE_FROM_DATA',
    'DataAttributeType',
    'FILE_STRING_CHOICE',
    'FileStringType',
    'NO_LIMIT',
    'Prototype',
    'PROTOTYPE',
    'YearFilterMonthsType',
    ]


api_attribute_map: dict[str, str] = {}
"""
Mapping from library attribute names to names used in the API.

It is used to convert fields in parameters ``sort`` and ``filters``.
Users should prefer to use keys of this dict in the two parameters.

The value is available if module `request_processor` or any module which
uses it is imported (e.g. root package or `query`).

Accessible through the package root namespace.
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

DataAttributeType = Union[str, int, datetime, date, None]
"""Type of `APIResource` data attribute."""

FILE_STRING_CHOICE = ('json', 'package', 'xhtml')
"""String valid for ``files`` parameter of download methods."""

FileStringType = Literal['json', 'package', 'xhtml']
"""String used in ``files`` parameter of download methods."""

NO_LIMIT = 0
"""
Fetches all filings that match the query.

Used as a value to the parameter ``limit``.

Accessible through the package root namespace.
"""

class Prototype:
    """Type of special value `PROTOTYPE`."""

PROTOTYPE = Prototype()
"""A special value for APIResource to construct a dummy instance."""

YearFilterMonthsType = tuple[tuple[int, int], tuple[int, int]]
"""Months chosen when only a year is given in a date filter."""
