"""Define tests for short date filters of query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from calendar import Calendar
from datetime import date, timezone

import pytest
import responses
from responses import matchers

import xbrl_filings_api as xf

UTC = timezone.utc

pytestmark = [pytest.mark.multifilter, pytest.mark.date]


def test_last_end_date_only_year(
        multifilter_belgium20_short_date_year_response, monkeypatch):
    """
    Test getting Belgian filings for financial year 2020, max_size=100.
    """
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
    """
    Test getting Belgian filings for financial year 2020,
    max_size=NO_LIMIT.
    """
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


def test_last_end_date_only_year_as_int(
        multifilter_belgium20_short_date_year_response, monkeypatch):
    """
    Test getting Belgian filings for financial year 2020, filter value
    int, max_size=100.
    """
    e_dates_with_filings = {date(2020, 12, 31), date(2021, 3, 31)}
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 8), (1, 8)))
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    fs = xf.get_filings(
        filters={
            'last_end_date': 2020,
            'country': 'BE'
            },
        sort=None,
        max_size=100,
        flags=xf.GET_ONLY_FILINGS
        )
    assert len(fs) >= 31
    last_end_dates = {filing.last_end_date for filing in fs}
    assert last_end_dates == e_dates_with_filings


def test_last_end_date_only_year_jan_to_dec(monkeypatch):
    """Test correct URL params for last_end_date Jan to Dec in 2024."""
    e_year = 2024
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 1), (1, 1)))
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    page_json = {
        'data': [], 'meta': {'count': 0}, 'jsonapi': {'version': '1.0'}}
    cal = Calendar()
    with responses.RequestsMock() as rsps:
        for month_num in range(1, 13):
            last_day = max(cal.itermonthdays(e_year, month_num))
            # period_end = last_end_date
            param_matcher = matchers.query_param_matcher({
                'page[size]': '100',
                'filter[period_end]': f'{e_year}-{month_num:02}-{last_day}'
                })
            rsps.get(
                url='https://filings.xbrl.org/api/filings',
                json=page_json,
                match=[param_matcher]
                )
        fs = xf.get_filings(
            filters={
                'last_end_date': str(e_year)
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )
        assert len(fs) == 0


def test_last_end_date_only_year_earlier_dec_to_next_jan(monkeypatch):
    """
    Test correct URL params for last_end_date earlier Dec to next Jan
    (14 months) in 2024.
    """
    e_year = 2024
    monkeypatch.setattr(xf.options, 'year_filter_months', ((-1, 12), (1, 2)))
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    page_json = {
        'data': [], 'meta': {'count': 0}, 'jsonapi': {'version': '1.0'}}
    with responses.RequestsMock() as rsps:
        caliters = [
            (e_year-1, [12]),
            (e_year, range(1, 13)),
            (e_year+1, [1])
            ]
        cal = Calendar()
        for year_num, monthiter in caliters:
            for month_num in monthiter:
                last_day = max(cal.itermonthdays(year_num, month_num))
                # period_end = last_end_date
                param_matcher = matchers.query_param_matcher({
                    'page[size]': '100',
                    'filter[period_end]': (
                        f'{year_num}-{month_num:02}-{last_day}')
                    })
                rsps.get(
                    url='https://filings.xbrl.org/api/filings',
                    json=page_json,
                    match=[param_matcher]
                    )
        fs = xf.get_filings(
            filters={
                'last_end_date': str(e_year)
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )
        assert len(fs) == 0


def test_last_end_date_only_year_two_finyears(monkeypatch):
    """
    Test correct URL params for last_end_date in financial years 2023 &
    2024.
    """
    e_year = 2023
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 8), (2, 8)))
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    page_json = {
        'data': [], 'meta': {'count': 0}, 'jsonapi': {'version': '1.0'}}
    with responses.RequestsMock() as rsps:
        caliters = [
            (e_year, range(8, 13)),
            (e_year+1, range(1, 13)),
            (e_year+2, range(1, 8))
            ]
        cal = Calendar()
        for year_num, monthiter in caliters:
            for month_num in monthiter:
                last_day = max(cal.itermonthdays(year_num, month_num))
                # period_end = last_end_date
                param_matcher = matchers.query_param_matcher({
                    'page[size]': '100',
                    'filter[period_end]': (
                        f'{year_num}-{month_num:02}-{last_day}')
                    })
                rsps.get(
                    url='https://filings.xbrl.org/api/filings',
                    json=page_json,
                    match=[param_matcher]
                    )
        fs = xf.get_filings(
            filters={
                'last_end_date': str(e_year)
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )
        assert len(fs) == 0


def test_raises_only_year_options_year_filter_months_start_month0(monkeypatch):
    """Test raising for options.year_filter_months start has month 0."""
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 0), (1, 12)))
    with pytest.raises(
            expected_exception=ValueError,
            match=r'options\.year_filter_months start month definition must '
                  r'be in 1\.\.12'):
        _ = xf.get_filings(
            filters={
                'last_end_date': '2024'
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )


def test_raises_only_year_options_year_filter_months_stop_month13(monkeypatch):
    """Test raising for options.year_filter_months stop has month 13."""
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 1), (1, 13)))
    with pytest.raises(
            expected_exception=ValueError,
            match=r'options\.year_filter_months stop month definition must be '
                  r'in 1\.\.12'):
        _ = xf.get_filings(
            filters={
                'last_end_date': '2024'
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )


def test_last_end_date_year_and_month(monkeypatch):
    """Test correct URL params for last_end_date in Feb 2024."""
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    page_json = {
        'data': [], 'meta': {'count': 0}, 'jsonapi': {'version': '1.0'}}
    with responses.RequestsMock() as rsps:
        # period_end = last_end_date
        param_matcher = matchers.query_param_matcher({
            'page[size]': '100',
            'filter[period_end]': '2024-02-29'
            })
        rsps.get(
            url='https://filings.xbrl.org/api/filings',
            json=page_json,
            match=[param_matcher]
            )
        fs = xf.get_filings(
            filters={
                'last_end_date': '2024-02'
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )
        assert len(fs) == 0


def test_raises_last_end_date_year_and_month_month0(monkeypatch):
    """Test raising for last_end_date month zero in 2024."""
    with pytest.raises(ValueError): # noqa: PT011 # msg from `datetime`
        _ = xf.get_filings(
            filters={
                'last_end_date': '2024-00'
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )


def test_raises_bad_options_year_filter_months(monkeypatch):
    """Test raising for bad options.year_filter_months."""
    monkeypatch.setattr(xf.options, 'year_filter_months', ((1, 8), (0, 8)))
    with pytest.raises(
            ValueError,
            match=(r'The option year_filter_months stop \(2nd item\) is '
                   r'before or equal to start \(1st item\)')):
        _ = xf.get_filings(
            filters={
                'last_end_date': '2020'
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )


def test_raises_too_many_date_parts(monkeypatch):
    """Test raising for date query of '2021-01-01-12'."""
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 8), (1, 8)))
    with pytest.raises(
            ValueError,
            match=(r'Date in filter field "last_end_date" is not a valid date '
                   r'or short date, value: "2021-01-01-12"')):
        _ = xf.get_filings(
            filters={
                'last_end_date': '2021-01-01-12'
                },
            sort=None,
            max_size=100,
            flags=xf.GET_ONLY_FILINGS
            )
