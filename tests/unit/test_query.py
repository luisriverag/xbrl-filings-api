"""Define tests for query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import os
import sqlite3
from datetime import date, datetime, timezone

import pytest
import requests

from xbrl_filings_api import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    APIError,
    Entity,
    Filing,
    FilingsPage,
    ValidationMessage,
    options,
    query,
)
from xbrl_filings_api.exceptions import FilterNotSupportedWarning

UTC = timezone.utc


def _db_record_count(cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0]


def test_get_filings(asml22en_response):
    """Requested filing is returned."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = query.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_ONLY_FILINGS
        )
    asml22 = next(iter(fs), None)
    assert isinstance(asml22, Filing), 'Filing is returned'

@pytest.mark.sqlite
def test_to_sqlite(asml22en_response, tmp_path, monkeypatch):
    """Requested filing is inserted into a database."""
    monkeypatch.setattr(options, 'views', None)
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    db_path = tmp_path / 'test_to_sqlite.db'
    query.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_ONLY_FILINGS
        )
    assert os.access(db_path, os.F_OK), 'Database file is created'
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM Filing WHERE filing_index = ?",
        (asml22_fxo,)
        )
    assert cur.fetchone() == (1,), 'Fetched record ends up in the database'
    assert _db_record_count(cur) == 1

@pytest.mark.paging
def test_filing_page_iter(asml22en_response):
    """Requested filing is returned on a filing page."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    piter = query.filing_page_iter(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_ONLY_FILINGS
        )
    page = next(piter, None)
    assert isinstance(page, FilingsPage), 'First iteration returns a page'
    asml22 = next(iter(page.filing_list), None)
    assert isinstance(asml22, Filing), 'Filing is returned on a page'
