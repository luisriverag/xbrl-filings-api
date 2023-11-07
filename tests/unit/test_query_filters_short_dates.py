"""
Define tests for single filters of query functions.

Single filter is a literal value for filter, unlike multifilter
(iterable of literals) or date filter (ISO date string or date object).
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import os
import sqlite3
from datetime import date, datetime, timezone

import pytest

from xbrl_filings_api import (
    GET_ONLY_FILINGS,
    APIError,
    Filing,
    options,
    query,
)
from xbrl_filings_api.exceptions import FilterNotSupportedWarning

UTC = timezone.utc


def _db_record_count(cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0]


# to_sqlite
# filing_page_iter
