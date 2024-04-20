"""Define enum `ScopeFlag`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from enum import Flag, auto

__all__ = ['ScopeFlag']


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
