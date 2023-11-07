"""Define tests for handling of filing pages in query functions."""

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
    monkeypatch.setattr(options, 'max_page_size', 2)
    piter = query.filing_page_iter(
        filters={
            'country': 'SE'
            },
        sort='added_time',
        max_size=5,
        flags=GET_ONLY_FILINGS
        )
    page1 = next(piter, None)
    assert isinstance(page1, FilingsPage), 'Pages are returned'
    page2 = next(piter, None)
    assert isinstance(page2, FilingsPage), '3 pages are returned'
    page3 = next(piter, None)
    assert isinstance(page3, FilingsPage), '3 pages are returned'
    page_none = next(piter, None)
    assert page_none is None, 'No more than 3 pages are returned'


# def test_filing_page_iter_filings_count(s,
        # multipage_response, monkeypatch):
    # """Function returns correct number of filings."""
    # monkeypatch.setattr(options, 'max_page_size', 2)
    # piter = query.filing_page_iter(
        # filters={
            # 'country': 'SE'
            # },
        # sort='added_time',
        # max_size=5,
        # flags=GET_ONLY_FILINGS
        # )
    # for i, page in enumerate(piter):
        # if i < 2:
            # assert len(page.filing_list) == 2, f'Page {i+1} is full with 2 filings'
        # elif i == 2:
            # assert len(page.filing_list) == 1, 'Third page has one filing'
