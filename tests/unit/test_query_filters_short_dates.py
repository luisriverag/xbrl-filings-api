"""Define tests for short date filters of query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import os
import sqlite3
from datetime import date, datetime, timezone

import pytest

import xbrl_filings_api as xf

UTC = timezone.utc


def _db_record_count(cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0]


# to_sqlite
# filing_page_iter
