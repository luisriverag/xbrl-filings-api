"""Enums for the package."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from enum import Enum, Flag, auto

__all__ = [
    'ScopeFlag',
    '_ParseType',
    ]


class ScopeFlag(Flag):
    """
    Flags for API resource retrieval scope.

    Use ``GET_ONLY_FILINGS`` alone, the rest alone or the rest combined
    (binary OR operator ``|``).
    """

    GET_ONLY_FILINGS = auto()
    """
    Retrieve only filings and nothing else. Overrides other flags.

    Accessible through the package root namespace.
    """

    GET_ENTITY = auto()
    """
    Retrieve entities of filings.

    Accessible through the package root namespace.
    """

    GET_VALIDATION_MESSAGES = auto()
    """
    Retrieve validation messages of filings.

    Accessible through the package root namespace.
    """


class _ParseType(Enum):
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
