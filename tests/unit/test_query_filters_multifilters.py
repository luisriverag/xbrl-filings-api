"""Define tests for query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import os
import sqlite3
from datetime import datetime, timezone

import pytest

from xbrl_filings_api import (
    GET_ONLY_FILINGS,
    APIError,
    options,
    query,
)
from xbrl_filings_api.exceptions import FilterNotSupportedWarning

UTC = timezone.utc


def _db_record_count(cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0]


def test_get_filings_api_id(api_id_multifilter_response):
    """Requested `api_id` filings are returned."""
    shell_api_ids = '1134', '1135', '4496', '4529'
    fs = query.get_filings(
        filters={
            'api_id': shell_api_ids
            },
        sort=None,
        max_size=4,
        flags=GET_ONLY_FILINGS
        )
    received_api_ids = {filing.api_id for filing in fs}
    assert received_api_ids == set(shell_api_ids)


def test_to_sqlite_api_id(
        api_id_multifilter_response, tmp_path, monkeypatch):
    """Filtering by `api_id` inserted to db."""
    monkeypatch.setattr(options, 'views', None)
    shell_api_ids = '1134', '1135', '4496', '4529'
    db_path = tmp_path / 'test_to_sqlite_api_id.db'
    query.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'api_id': shell_api_ids
            },
        sort=None,
        max_size=4,
        flags=GET_ONLY_FILINGS
        )
    assert os.access(db_path, os.F_OK), 'Database file is created'
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT api_id FROM Filing "
        "WHERE api_id IN (?, ?, ?, ?)",
        shell_api_ids
        )
    saved_ids = {row[0] for row in cur.fetchall()}
    assert saved_ids == set(shell_api_ids)
    assert _db_record_count(cur) == 4


def test_get_filings_country_only_first(country_multifilter_response):
    """Requested `country` filings are returned."""
    country_codes = ['FI', 'SE', 'NO']
    fs = query.get_filings(
        filters={
            'country': country_codes
            },
        sort=None,
        max_size=3,
        flags=GET_ONLY_FILINGS
        )
    assert len(fs) == 3, 'Requested number of filings returned'
    received_countries = {filing.country for filing in fs}
    assert 'FI' in received_countries, 'Only FI available, match count'
    assert 'SE' not in received_countries, 'Too many FI filings'
    assert 'NO' not in received_countries, 'Too many FI filings'


def test_to_sqlite_country_only_first(
        country_multifilter_response, tmp_path, monkeypatch):
    """Filtering by `country` filings inserted to db."""
    monkeypatch.setattr(options, 'views', None)
    country_codes = ['FI', 'SE', 'NO']
    db_path = tmp_path / 'test_to_sqlite_country_only_first.db'
    query.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'country': country_codes
            },
        sort=None,
        max_size=3,
        flags=GET_ONLY_FILINGS
        )
    assert os.access(db_path, os.F_OK), 'Database file is created'
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT country FROM Filing "
        "WHERE country IN (?, ?, ?)",
        country_codes
        )
    saved_countries = {row[0] for row in cur.fetchall()}
    assert saved_countries == {'FI'}
    assert _db_record_count(cur) == 3


def test_get_filings_filing_index(
        filing_index_multifilter_response):
    """Requested `filing_index` filings are returned."""
    filing_index_codes = (
        '21380068P1DRHMJ8KU70-2021-12-31-ESEF-GB-0',
        '21380068P1DRHMJ8KU70-2021-12-31-ESEF-NL-0'
        )
    fs = query.get_filings(
        filters={
            'filing_index': filing_index_codes
            },
        sort=None,
        max_size=2,
        flags=GET_ONLY_FILINGS
        )
    received_countries = {filing.filing_index for filing in fs}
    assert received_countries == set(filing_index_codes)


def test_to_sqlite_filing_index(
        filing_index_multifilter_response, tmp_path, monkeypatch):
    """Filtering by `filing_index` filings inserted to db."""
    monkeypatch.setattr(options, 'views', None)
    filing_index_codes = (
        '21380068P1DRHMJ8KU70-2021-12-31-ESEF-GB-0',
        '21380068P1DRHMJ8KU70-2021-12-31-ESEF-NL-0'
        )
    db_path = tmp_path / 'test_to_sqlite_filing_index.db'
    query.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'filing_index': filing_index_codes
            },
        sort=None,
        max_size=2,
        flags=GET_ONLY_FILINGS
        )
    assert os.access(db_path, os.F_OK), 'Database file is created'
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT filing_index FROM Filing "
        "WHERE filing_index IN (?, ?)",
        filing_index_codes
        )
    saved_fxo = {row[0] for row in cur.fetchall()}
    assert saved_fxo == set(filing_index_codes)
    assert _db_record_count(cur) == 2


def test_get_filings_reporting_date(reporting_date_multifilter_response):
    """APIError raised for filtering with `reporting_date`."""
    dates = '2020-12-31', '2021-12-31', '2022-12-31'
    with pytest.raises(APIError, match='FilingSchema has no attribute'):
        with pytest.warns(FilterNotSupportedWarning):
            _ = query.get_filings(
                filters={
                    'reporting_date': dates
                    },
                sort=None,
                max_size=3,
                flags=GET_ONLY_FILINGS
                )


def test_to_sqlite_reporting_date(
        reporting_date_multifilter_response, tmp_path, monkeypatch):
    """Filtering by `reporting_date` raises exception."""
    monkeypatch.setattr(options, 'views', None)
    dates = '2020-12-31', '2021-12-31', '2022-12-31'
    db_path = tmp_path / 'test_to_sqlite_reporting_date.db'
    with pytest.raises(APIError, match='FilingSchema has no attribute'):
        with pytest.warns(FilterNotSupportedWarning):
            query.to_sqlite(
                path=db_path,
                update=False,
                filters={
                    'reporting_date': dates
                    },
                sort=None,
                max_size=3,
                flags=GET_ONLY_FILINGS
                )
    assert not os.access(db_path, os.F_OK), 'Database file is not created'


@pytest.mark.xfail(
    reason=(
        'Filtering by "_count" attributes is not supported by the '
        'API.'
        ),
    raises=APIError)
def test_get_filings_inconsistency_count(
        inconsistency_count_multifilter_response):
    """Requested `inconsistency_count` filings are returned."""
    ic_counts = 1, 2
    fs = query.get_filings(
        filters={
            'inconsistency_count': ic_counts
            },
        sort=None,
        max_size=2,
        flags=GET_ONLY_FILINGS
        )
    received_counts = tuple(filing.inconsistency_count for filing in fs)
    assert received_counts == 1, 1


@pytest.mark.xfail(
    reason=(
        'Filtering by "_count" attributes is not supported by the '
        'API.'
        ),
    raises=APIError)
def test_to_sqlite_inconsistency_count(
        inconsistency_count_multifilter_response, tmp_path, monkeypatch
        ):
    """Filtering by `inconsistency_count` filings inserted to db."""
    monkeypatch.setattr(options, 'views', None)
    ic_counts = 1, 2
    db_path = tmp_path / 'test_to_sqlite_inconsistency_count.db'
    query.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'inconsistency_count': ic_counts
            },
        sort=None,
        max_size=2,
        flags=GET_ONLY_FILINGS
        )
    assert os.access(db_path, os.F_OK), 'Database file is created'
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT inconsistency_count FROM Filing "
        "WHERE inconsistency_count IN (?, ?)",
        ic_counts
        )
    saved_ic_counts = {row[0] for row in cur.fetchall()}
    assert saved_ic_counts == set(ic_counts)
    assert _db_record_count(cur) == 2


def test_get_filings_processed_time_str(
        processed_time_multifilter_response):
    """Filtering by `processed_time` as str returns 2 filings."""
    cloetta_sv_strs = (
        '2023-01-18 11:02:06.724768',
        '2023-05-16 21:07:17.825836'
        )
    cloetta_sv_objs = (
        datetime(2023, 1, 18, 11, 2, 6, 724768, tzinfo=UTC),
        datetime(2023, 5, 16, 21, 7, 17, 825836, tzinfo=UTC)
        )
    fs = query.get_filings(
        filters={
            'processed_time': cloetta_sv_strs
            },
        sort=None,
        max_size=2,
        flags=GET_ONLY_FILINGS
        )
    received_dts = {filing.processed_time for filing in fs}
    assert cloetta_sv_objs[0] in received_dts
    assert cloetta_sv_objs[1] in received_dts
    assert len(received_dts) == 2
    received_strs = {filing.processed_time_str for filing in fs}
    assert cloetta_sv_strs[0] in received_strs
    assert cloetta_sv_strs[1] in received_strs


def test_to_sqlite_processed_time_str(
        processed_time_multifilter_response, tmp_path, monkeypatch
        ):
    """Filtering by `processed_time` filings inserted to db."""
    monkeypatch.setattr(options, 'views', None)
    cloetta_sv_strs = (
        '2023-01-18 11:02:06.724768',
        '2023-05-16 21:07:17.825836'
        )
    db_path = tmp_path / 'test_to_sqlite_processed_time_str.db'
    query.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'processed_time': cloetta_sv_strs
            },
        sort=None,
        max_size=2,
        flags=GET_ONLY_FILINGS
        )
    assert os.access(db_path, os.F_OK), 'Database file is created'
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT processed_time FROM Filing "
        "WHERE processed_time IN (?, ?)",
        cloetta_sv_strs
        )
    saved_proc_times = {row[0] for row in cur.fetchall()}
    assert saved_proc_times == set(cloetta_sv_strs)
    assert _db_record_count(cur) == 2


# filing_page_iter
