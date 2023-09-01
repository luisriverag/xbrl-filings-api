"""
Enums for the package.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from enum import Enum, Flag, auto

NO_LIMIT = 0


class ParseType(Enum):
    DATE = auto()
    DATETIME = auto()
    URL = auto()


class ScopeFlag(Flag):
    GET_ONLY_FILINGS = auto()
    GET_ENTITY = auto()
    GET_VALIDATION_MESSAGES = auto()


GET_ONLY_FILINGS = ScopeFlag.GET_ONLY_FILINGS
GET_ENTITY = ScopeFlag.GET_ENTITY
GET_VALIDATION_MESSAGES = ScopeFlag.GET_VALIDATION_MESSAGES
