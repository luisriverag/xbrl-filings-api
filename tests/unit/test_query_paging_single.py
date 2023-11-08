"""Define tests for handling of filing pages in query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import sqlite3

import pytest
import requests

import xbrl_filings_api as xf


def _db_record_count(cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0]


@pytest.mark.xfail(
    reason=(
        'Error in undelying API: redundant filings on pages. '
        'Filing with api_id "1" (Cloetta AB, 2021, en) and "2" '
        '(Cloetta AB, 2021, sv) is returned twice and as a result, '
        'a fouth page is requested to fulfil expected 5 filings.'
        ),
    raises=requests.ConnectionError
    )
def test_filing_page_iter(multipage_lax_response, monkeypatch):
    """Requested filings are available on 3 pages."""
    monkeypatch.setattr(xf.options, 'max_page_size', 2)
    piter = xf.filing_page_iter(
        filters={
            'country': 'SE'
            },
        sort='added_time',
        max_size=5,
        flags=xf.GET_ONLY_FILINGS
        )
    page1 = next(piter, None)
    assert isinstance(page1, xf.FilingsPage), 'Pages are returned'
    page2 = next(piter, None)
    assert isinstance(page2, xf.FilingsPage), '3 pages are returned'
    page3 = next(piter, None)
    assert isinstance(page3, xf.FilingsPage), '3 pages are returned'
    page_none = next(piter, None)
    assert page_none is None, 'No more than 3 pages are returned'
