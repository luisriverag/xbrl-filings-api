"""
Define tests for `stats` of the root library.

Not to be confused with the `stats` of the downloader submodule.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest
import responses

import xbrl_filings_api as xf
import xbrl_filings_api.stats as stats


@pytest.mark.date
@pytest.mark.paging
def test_no_limit(paging_czechia20dec_response, monkeypatch):
    """Test max_size=NO_LIMIT for stats counters."""
    monkeypatch.setattr(xf.options, 'max_page_size', 10)
    monkeypatch.setattr(stats, 'query_call_counter', 0)
    monkeypatch.setattr(stats, 'api_query_counter', 0)
    monkeypatch.setattr(stats, 'page_counter', 0)
    # The database has 29 records for this query
    _ = xf.get_filings(
        filters={
            'country': 'CZ',
            'last_end_date': '2020-12-31',
            },
        sort=None,
        max_size=xf.NO_LIMIT,
        flags=xf.GET_ONLY_FILINGS
        )
    assert stats.query_call_counter == 1
    assert stats.api_query_counter == 1
    assert stats.page_counter == 3


@pytest.mark.paging
def test_max_size_limited(
        paging_oldest_ukrainian_2pg_4ea_response, monkeypatch):
    """Test limited results for stats counters."""
    monkeypatch.setattr(xf.options, 'max_page_size', 4)
    monkeypatch.setattr(stats, 'query_call_counter', 0)
    monkeypatch.setattr(stats, 'api_query_counter', 0)
    monkeypatch.setattr(stats, 'page_counter', 0)
    # The database has 29 records for this query
    _ = xf.get_filings(
        filters={
            'country': 'UA'
            },
        sort=['last_end_date', 'processed_time'],
        max_size=8,
        flags=xf.GET_ONLY_FILINGS
        )
    assert stats.query_call_counter == 1
    assert stats.api_query_counter == 1
    assert stats.page_counter == 2


@pytest.mark.multifilter
def test_multifilter(multifilter_api_id_response, monkeypatch):
    """Test multifilter for stats counters."""
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    monkeypatch.setattr(stats, 'query_call_counter', 0)
    monkeypatch.setattr(stats, 'api_query_counter', 0)
    monkeypatch.setattr(stats, 'page_counter', 0)
    shell_api_ids = '1134', '1135', '4496', '4529'
    _ = xf.get_filings(
        filters={
            'api_id': shell_api_ids
            },
        sort=None,
        max_size=4,
        flags=xf.GET_ONLY_FILINGS
        )
    assert stats.query_call_counter == 1
    assert stats.api_query_counter == 4
    assert stats.page_counter == 4


@pytest.mark.multifilter
@pytest.mark.date
def test_short_date(
        multifilter_belgium20_short_date_year_response, monkeypatch):
    """Test short date for stats counters."""
    monkeypatch.setattr(xf.options, 'year_filter_months', ((0, 8), (1, 8)))
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    monkeypatch.setattr(stats, 'query_call_counter', 0)
    monkeypatch.setattr(stats, 'api_query_counter', 0)
    monkeypatch.setattr(stats, 'page_counter', 0)
    _ = xf.get_filings(
        filters={
            'last_end_date': 2020,
            'country': 'BE'
            },
        sort=None,
        max_size=100,
        flags=xf.GET_ONLY_FILINGS
        )
    assert stats.query_call_counter == 1
    assert stats.api_query_counter == 12
    assert stats.page_counter == 12


def test_two_query_calls(urlmock, monkeypatch):
    """Test two query calls for stats counters."""
    monkeypatch.setattr(xf.options, 'max_page_size', 200)
    monkeypatch.setattr(stats, 'query_call_counter', 0)
    monkeypatch.setattr(stats, 'api_query_counter', 0)
    monkeypatch.setattr(stats, 'page_counter', 0)
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'creditsuisse21en_by_id')
        urlmock.apply(rsps, 'asml22en')

        creditsuisse21en_api_id = '162'
        _ = xf.get_filings(
            filters={
                'api_id': creditsuisse21en_api_id
                },
            sort=None,
            max_size=1,
            flags=xf.GET_ONLY_FILINGS
            )
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        _ = xf.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=xf.GET_ONLY_FILINGS
            )
    assert stats.query_call_counter == 2
    assert stats.api_query_counter == 2
    assert stats.page_counter == 2
