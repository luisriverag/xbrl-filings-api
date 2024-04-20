"""Define enum `ParseType`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from enum import Enum, auto

__all__ = ['ParseType']


class ParseType(Enum):
    """Parsing selection for dot access paths in API response."""

    DATE = auto()
    """Parsed into :class:`datetime.date`."""

    DATETIME = auto()
    """
    Parsed into timezone-aware :class:`~datetime.datetime`.

    Timezone will be the one specified in the string or UTC, if
    unspecified.
    """

    URL = auto()
    """Relative URLs will be parsed into absolute URLs."""
