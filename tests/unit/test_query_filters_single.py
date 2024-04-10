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

import sqlite3
from datetime import date, datetime, timezone

import pytest

import xbrl_filings_api as xf

UTC = timezone.utc


def test_get_filings_api_id(creditsuisse21en_by_id_response):
    """Requested `api_id` is returned."""
    creditsuisse21en_api_id = '162'
    fs = xf.get_filings(
        filters={
            'api_id': creditsuisse21en_api_id
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    creditsuisse21 = next(iter(fs), None)
    assert isinstance(creditsuisse21, xf.Filing)
    assert creditsuisse21.api_id == creditsuisse21en_api_id


@pytest.mark.sqlite
def test_to_sqlite_api_id(
    creditsuisse21en_by_id_response, db_record_count, tmp_path, monkeypatch):
    """Requested `api_id` is inserted into a database."""
    monkeypatch.setattr(xf.options, 'views', None)
    creditsuisse21en_api_id = '162'
    db_path = tmp_path / 'test_to_sqlite_api_id.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'api_id': creditsuisse21en_api_id
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM Filing WHERE api_id = ?",
        (creditsuisse21en_api_id,)
        )
    assert cur.fetchone() == (1,), 'Inserted requested filing(s)'
    assert db_record_count(cur) == 1
    con.close()


def test_get_filings_filing_index(asml22en_response):
    """Requested `filing_index` is returned."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    asml22 = next(iter(fs), None)
    assert isinstance(asml22, xf.Filing)
    assert asml22.filing_index == asml22_fxo


@pytest.mark.sqlite
def test_to_sqlite_filing_index(
        asml22en_response, db_record_count, tmp_path, monkeypatch):
    """Requested `filing_index` is inserted into a database."""
    monkeypatch.setattr(xf.options, 'views', None)
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    db_path = tmp_path / 'test_to_sqlite_filing_index.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM Filing WHERE filing_index = ?",
        (asml22_fxo,)
        )
    assert cur.fetchone() == (1,), 'Inserted requested filing(s)'
    assert db_record_count(cur) == 1
    con.close()


def test_get_filings_language(filter_language_response):
    """Filter `language` raises an `APIError`."""
    with pytest.raises(xf.APIError, match=r'Bad filter value'):
        with pytest.warns(xf.FilterNotSupportedWarning):
            _ = xf.get_filings(
                filters={
                    'language': 'fi'
                    },
                sort=None,
                limit=1,
                flags=xf.GET_ONLY_FILINGS
                )


@pytest.mark.sqlite
def test_to_sqlite_language(
    filter_language_response, tmp_path, monkeypatch):
    """Filter `language` raises an `APIError` for to_sqlite."""
    monkeypatch.setattr(xf.options, 'views', None)
    db_path = tmp_path / 'test_to_sqlite_language.db'
    with pytest.raises(xf.APIError, match=r'Bad filter value'):
        with pytest.warns(xf.FilterNotSupportedWarning):
            xf.to_sqlite(
                path=db_path,
                update=False,
                filters={
                    'language': 'fi'
                    },
                sort=None,
                limit=1,
                flags=xf.GET_ONLY_FILINGS
                )
    assert not db_path.is_file()


@pytest.mark.date
def test_get_filings_last_end_date_str(filter_last_end_date_response):
    """String filtered `last_end_date` returns filing(s)."""
    date_str = '2021-02-28'
    fs = xf.get_filings(
        filters={
            'last_end_date': date_str
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    agrana20 = next(iter(fs), None)
    assert isinstance(agrana20, xf.Filing)
    expected_date = date(*[int(pt) for pt in date_str.split('-')])
    assert agrana20.last_end_date == expected_date


@pytest.mark.sqlite
@pytest.mark.date
def test_to_sqlite_last_end_date_str(
        filter_last_end_date_response, db_record_count, tmp_path, monkeypatch):
    """String filtered `last_end_date` is inserted into a database."""
    monkeypatch.setattr(xf.options, 'views', None)
    date_str = '2021-02-28'
    db_path = tmp_path / 'test_to_sqlite_last_end_date.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'last_end_date': date_str
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM Filing WHERE last_end_date = ?",
        (date_str,)
        )
    count_num = cur.fetchone()[0]
    assert count_num == 1, 'Inserted requested filing(s)'
    assert db_record_count(cur) == 1
    con.close()


@pytest.mark.date
def test_get_filings_last_end_date_obj(filter_last_end_date_response):
    """Date object filtered `last_end_date` returns filing(s)."""
    date_obj = date(2021, 2, 28)
    fs = xf.get_filings(
        filters={
            'last_end_date': date_obj
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    agrana20 = next(iter(fs), None)
    assert isinstance(agrana20, xf.Filing)
    assert agrana20.last_end_date == date_obj


@pytest.mark.sqlite
@pytest.mark.date
def test_to_sqlite_last_end_date_obj(
        filter_last_end_date_response, db_record_count, tmp_path, monkeypatch):
    """
    Date object filtered `last_end_date` is inserted into a database.
    """
    monkeypatch.setattr(xf.options, 'views', None)
    date_obj = date(2021, 2, 28)
    db_path = tmp_path / 'test_to_sqlite_last_end_date.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'last_end_date': date_obj
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM Filing WHERE last_end_date = ?",
        (date_obj.strftime('%Y-%m-%d'),)
        )
    count_num = cur.fetchone()[0]
    assert count_num == 1, 'Inserted requested filing(s)'
    assert db_record_count(cur) == 1
    con.close()


@pytest.mark.date
def test_get_filings_last_end_date_datetime(
        filter_last_end_date_lax_response):
    """Datetime filtered `last_end_date` raises ValueError."""
    dt_obj = datetime(2021, 2, 28, tzinfo=UTC)
    with pytest.raises(
        expected_exception=ValueError,
        match=r'Not possible to filter date field "\w+" by datetime'
        ):
        _ = xf.get_filings(
            filters={
                'last_end_date': dt_obj
                },
            sort=None,
            limit=1,
            flags=xf.GET_ONLY_FILINGS
            )


@pytest.mark.sqlite
@pytest.mark.date
def test_to_sqlite_last_end_date_datetime(
        filter_last_end_date_lax_response, tmp_path, monkeypatch
        ):
    """Datetime filtered `last_end_date` is inserted into a database."""
    monkeypatch.setattr(xf.options, 'views', None)
    dt_obj = datetime(2021, 2, 28, tzinfo=UTC)
    db_path = tmp_path / 'test_to_sqlite_last_end_date.db'
    with pytest.raises(
        expected_exception=ValueError,
        match=r'Not possible to filter date field "\w+" by datetime'
        ):
        xf.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'last_end_date': dt_obj
                },
            sort=None,
            limit=1,
            flags=xf.GET_ONLY_FILINGS
            )


@pytest.mark.datetime
def test_get_filings_added_time_str_datelike(
        filter_added_time_response, monkeypatch):
    """String filtered date-like `added_time` returns filing(s)."""
    time_str = '2021-09-23 00:00:00'
    time_utc = datetime(2021, 9, 23, tzinfo=UTC)
    fs = xf.get_filings(
        filters={
            'added_time': time_str
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    vtbbank20 = next(iter(fs), None)
    assert isinstance(vtbbank20, xf.Filing)
    assert vtbbank20.added_time_str == time_str
    assert vtbbank20.added_time == time_utc


@pytest.mark.datetime
def test_get_filings_added_time_str_exact(
        filter_added_time_2_response, monkeypatch):
    """String filtered exact `added_time` returns filing(s)."""
    time_str = '2023-05-09 13:27:02.676029'
    time_utc = datetime(2023, 5, 9, 13, 27, 2, 676029, tzinfo=UTC)
    fs = xf.get_filings(
        filters={
            'added_time': time_str
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    vtbbank20 = next(iter(fs), None)
    assert isinstance(vtbbank20, xf.Filing)
    assert vtbbank20.added_time_str == time_str
    assert vtbbank20.added_time == time_utc


@pytest.mark.sqlite
@pytest.mark.datetime
def test_to_sqlite_added_time_str_exact(
        filter_added_time_2_response, db_record_count, tmp_path, monkeypatch):
    """String filtered `added_time` is inserted into a database."""
    monkeypatch.setattr(xf.options, 'views', None)
    time_str = '2023-05-09 13:27:02.676029'
    db_path = tmp_path / 'test_to_sqlite_added_time_str_exact.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'added_time': time_str
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT count(*) FROM Filing WHERE added_time = ?",
        (time_str,)
        )
    correct_count = cur.fetchone()[0]
    assert correct_count == 1, 'Inserted filing'
    assert db_record_count(cur) == 1
    con.close()


@pytest.mark.datetime
def test_get_filings_added_time_datetime_utc(
        filter_added_time_2_response, monkeypatch):
    """Datetime (UTC) filtered `added_time` returns filing(s)."""
    dt_obj = datetime(2023, 5, 9, 13, 27, 2, 676029, tzinfo=UTC)
    time_str = '2023-05-09 13:27:02.676029'
    fs = xf.get_filings(
        filters={
            'added_time': dt_obj
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    vtbbank20 = next(iter(fs), None)
    assert isinstance(vtbbank20, xf.Filing)
    assert vtbbank20.added_time == dt_obj
    assert vtbbank20.added_time_str == time_str


@pytest.mark.sqlite
@pytest.mark.datetime
def test_to_sqlite_added_time_datetime_utc(
        filter_added_time_2_response, db_record_count, tmp_path, monkeypatch):
    """
    Datetime (UTC) filtered `added_time` is inserted into a database.
    """
    monkeypatch.setattr(xf.options, 'views', None)
    dt_obj = datetime(2023, 5, 9, 13, 27, 2, 676029, tzinfo=UTC)
    e_time_str = '2023-05-09 13:27:02.676029'
    db_path = tmp_path / 'test_to_sqlite_added_time_datetime_utc.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'added_time': dt_obj
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT count(*) FROM Filing WHERE added_time = ?",
        (e_time_str,)
        )
    correct_count = cur.fetchone()[0]
    assert correct_count == 1, 'Inserted filing'
    assert db_record_count(cur) == 1
    con.close()


@pytest.mark.datetime
def test_get_filings_added_time_datetime_naive(
        filter_added_time_2_response, monkeypatch):
    """Datetime (naive) filtered `added_time` returns filing(s)."""
    dt_obj = datetime(2023, 5, 9, 13, 27, 2, 676029, tzinfo=None)
    time_str = '2023-05-09 13:27:02.676029'
    fs = xf.get_filings(
        filters={
            'added_time': dt_obj
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    vtbbank20 = next(iter(fs), None)
    assert isinstance(vtbbank20, xf.Filing)
    assert vtbbank20.added_time == dt_obj.replace(tzinfo=UTC)
    assert vtbbank20.added_time_str == time_str


@pytest.mark.datetime
def test_get_filings_added_time_date(filter_added_time_lax_response):
    """Date object filtered `added_time` raises ValueError."""
    date_obj = date(2021, 9, 23)
    with pytest.raises(
        expected_exception=ValueError,
        match=r'Not possible to filter datetime field "\w+" by date'
        ):
        _ = xf.get_filings(
            filters={
                'added_time': date_obj
                },
            sort=None,
            limit=1,
            flags=xf.GET_ONLY_FILINGS
            )


@pytest.mark.sqlite
@pytest.mark.datetime
def test_to_sqlite_added_time_date(
        filter_added_time_lax_response, tmp_path, monkeypatch):
    """
    Date object filtered `added_time` for database raises ValueError.
    """
    monkeypatch.setattr(xf.options, 'views', None)
    date_obj = date(2021, 9, 23)
    db_path = tmp_path / 'test_to_sqlite_added_time_date.db'
    with pytest.raises(
        expected_exception=ValueError,
        match=r'Not possible to filter datetime field "\w+" by date'
        ):
        xf.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'added_time': date_obj
                },
            sort=None,
            limit=1,
            flags=xf.GET_ONLY_FILINGS
            )
    assert not db_path.is_file()


@pytest.mark.datetime
def test_get_filings_added_time_bad_datetime(monkeypatch):
    """Test raising for bad string filtered `added_time`."""
    time_str = '2021-99-99 99:99:99'
    with pytest.raises(
            ValueError,
            match=(r'Not possible to parse datetime in filter field '
                   r'"added_time" string "2021-99-99 99:99:99"')):
        _ = xf.get_filings(
            filters={
                'added_time': time_str
                },
            sort=None,
            limit=1,
            flags=xf.GET_ONLY_FILINGS
            )


def test_get_filings_entity_api_id(filter_entity_api_id_lax_response):
    """Querying `entity_api_id` raises APIError."""
    kone_id = '2499'
    with pytest.raises(xf.APIError, match=r'FilingSchema has no attribute'):
        with pytest.warns(xf.FilterNotSupportedWarning):
            _ = xf.get_filings(
                filters={
                    'entity_api_id': kone_id
                    },
                sort=None,
                limit=1,
                flags=xf.GET_ONLY_FILINGS
                )


def test_get_filings_package_sha256(filter_package_sha256_response):
    """Querying `package_sha256` returns filing(s)."""
    filter_sha = (
        'e489a512976f55792c31026457e86c9176d258431f9ed645451caff9e4ef5f80')
    fs = xf.get_filings(
        filters={
            'package_sha256': filter_sha
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    kone22en = next(iter(fs), None)
    assert isinstance(kone22en, xf.Filing)
    assert kone22en.package_sha256 == filter_sha


@pytest.mark.sqlite
def test_to_sqlite_package_sha256(
        filter_package_sha256_response, db_record_count, tmp_path,
        monkeypatch):
    """Requested `package_sha256` is inserted into a database."""
    monkeypatch.setattr(xf.options, 'views', None)
    filter_sha = (
        'e489a512976f55792c31026457e86c9176d258431f9ed645451caff9e4ef5f80')
    db_path = tmp_path / 'test_to_sqlite_package_sha256.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'package_sha256': filter_sha
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM Filing WHERE package_sha256 = ?",
        (filter_sha,)
        )
    count_num = cur.fetchone()[0]
    assert count_num == 1, 'Inserted requested filing(s)'
    assert db_record_count(cur) == 1
    con.close()


@pytest.mark.date
def test_get_filings_2filters_country_last_end_date_str(
        finnish_jan22_response):
    """Filters `country` and `last_end_date` return 2 filings."""
    fs = xf.get_filings(
        filters={
            'country': 'FI',
            'last_end_date': '2022-01-31'
            },
        sort=None,
        limit=2,
        flags=xf.GET_ONLY_FILINGS
        )
    assert len(fs) == 2, 'Two reports issued in Finland for Jan 2022.'
    fxo_set = {filing.filing_index for filing in fs}
    assert len(fxo_set) == 2, 'Filings are unique'


@pytest.mark.sqlite
@pytest.mark.date
def test_to_sqlite_2filters_country_last_end_date_str(
        finnish_jan22_response, db_record_count, tmp_path, monkeypatch):
    """Filters `country` and `last_end_date` insert 2 filings to db."""
    monkeypatch.setattr(xf.options, 'views', None)
    db_path = (
        tmp_path / 'test_to_sqlite_2filters_country_last_end_date_str.db')
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'country': 'FI',
            'last_end_date': '2022-01-31'
            },
        sort=None,
        limit=2,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT filing_index FROM Filing "
        "WHERE country = ? AND last_end_date = ?",
        ('FI', '2022-01-31')
        )
    fxo_a = cur.fetchone()[0]
    fxo_b = cur.fetchone()[0]
    assert fxo_a != fxo_b, 'Filings are unique'
    assert cur.fetchone() is None, 'Two filings inserted'
    assert db_record_count(cur) == 2
    con.close()


@pytest.mark.date
def test_get_filings_2filters_country_last_end_date_date(
        finnish_jan22_response):
    """Filters `country` and `last_end_date` as date work."""
    fs = xf.get_filings(
        filters={
            'country': 'FI',
            'last_end_date': date(2022, 1, 31)
            },
        sort=None,
        limit=2,
        flags=xf.GET_ONLY_FILINGS
        )
    assert len(fs) == 2, 'Two reports issued in Finland for Jan 2022.'
    fxo_set = {filing.filing_index for filing in fs}
    assert len(fxo_set) == 2, 'Filings are unique'


@pytest.mark.sqlite
@pytest.mark.date
def test_to_sqlite_2filters_country_last_end_date_date(
    finnish_jan22_response, db_record_count, tmp_path, monkeypatch):
    """Filters `country` and `last_end_date` as date insert to db."""
    monkeypatch.setattr(xf.options, 'views', None)
    db_path = (
        tmp_path / 'test_to_sqlite_2filters_country_last_end_date_date.db')
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'country': 'FI',
            'last_end_date': date(2022, 1, 31)
            },
        sort=None,
        limit=2,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT filing_index FROM Filing "
        "WHERE country = ? AND last_end_date = ?",
        ('FI', '2022-01-31')
        )
    fxo_a = cur.fetchone()[0]
    fxo_b = cur.fetchone()[0]
    assert fxo_a != fxo_b, 'Filings are unique'
    assert cur.fetchone() is None, 'Two filings inserted'
    assert db_record_count(cur) == 2
    con.close()


def test_raises_get_filings_none_filter():
    """Test raising for filter value None."""
    with pytest.raises(
            ValueError,
            match=r'Value None is not allowed for filters, field "api_id"'):
        _ = xf.get_filings(
            filters={
                'api_id': None
                },
            sort=None,
            limit=4,
            flags=xf.GET_ONLY_FILINGS
            )
