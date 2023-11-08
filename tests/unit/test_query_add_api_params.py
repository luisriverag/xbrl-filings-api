"""Define tests for add_api_params parameter of query functions."""

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


def test_get_filings_override_max_size(asml22en_response):
    """`max_size` can be overridden with `add_api_params`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=10,
        flags=xf.GET_ONLY_FILINGS,
        add_api_params={'page[size]': '1'}
        )
    assert len(fs) == 1, 'Parameter max_size is overridden to be 1'


# to_sqlite
# filing_page_iter
