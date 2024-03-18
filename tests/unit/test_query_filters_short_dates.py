"""Define tests for short date filters of query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime, timezone

import pytest

import xbrl_filings_api as xf

UTC = timezone.utc

pytestmark = [pytest.mark.multifilter, pytest.mark.date]


def test_last_end_date_only_year(
        multifilter_belgium20_short_date_year_response, monkeypatch):
    """Test getting Belgian filings for financial year 2020, max_size=100."""
    e_dates_with_filings = {date(2020, 12, 31), date(2021, 3, 31)}
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 8), (1, 8)))
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    fs = xf.get_filings(
        filters={
            'last_end_date': '2020',
            'country': 'BE'
            },
        sort=None,
        max_size=100,
        flags=xf.GET_ONLY_FILINGS
        )
    assert len(fs) >= 31
    last_end_dates = {filing.last_end_date for filing in fs}
    assert last_end_dates == e_dates_with_filings


def test_last_end_date_only_year_no_limit(
        multifilter_belgium20_short_date_year_no_limit_response, monkeypatch):
    """Test getting Belgian filings for financial year 2020, max_size=NO_LIMIT."""
    e_dates_with_filings = {date(2020, 12, 31), date(2021, 3, 31)}
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 8), (1, 8)))
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    fs = xf.get_filings(
        filters={
            'last_end_date': '2020',
            'country': 'BE'
            },
        sort=None,
        max_size=xf.NO_LIMIT,
        flags=xf.GET_ONLY_FILINGS
        )
    assert len(fs) >= 31
    last_end_dates = {filing.last_end_date for filing in fs}
    assert last_end_dates == e_dates_with_filings
