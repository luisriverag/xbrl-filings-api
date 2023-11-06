"""Define tests for query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import os
import sqlite3
from datetime import date, datetime, timedelta, timezone

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


def _sql_total_count_is(expected_count, cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0] == expected_count


class TestFundamentalOperation:
    """Test fundamental operation."""

    def test_get_filings(s, asml22en_response):
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
    def test_to_sqlite(s, asml22en_response, tmp_path, monkeypatch):
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
        assert _sql_total_count_is(1, cur)

    @pytest.mark.paging
    def test_filing_page_iter(s, asml22en_response):
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


class TestParam_filters_single:
    """
    Test parameter `filters` using single filters.

    Single filter is a literal value for filter, unlike multifilter
    (iterable of literals) or date filter (ISO date string or date
    object).
    """

    def test_get_filings_api_id(s, creditsuisse21en_by_id_response):
        """Requested `api_id` is returned."""
        creditsuisse21en_api_id = '162'
        fs = query.get_filings(
            filters={
                'api_id': creditsuisse21en_api_id
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        creditsuisse21 = next(iter(fs), None)
        assert isinstance(creditsuisse21, Filing)
        assert creditsuisse21.api_id == creditsuisse21en_api_id

    @pytest.mark.sqlite
    def test_to_sqlite_api_id(
        s, creditsuisse21en_by_id_response, tmp_path, monkeypatch):
        """Requested `api_id` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        creditsuisse21en_api_id = '162'
        db_path = tmp_path / 'test_to_sqlite_api_id.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'api_id': creditsuisse21en_api_id
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE api_id = ?",
            (creditsuisse21en_api_id,)
            )
        assert cur.fetchone() == (1,), 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_filing_index(s, asml22en_response):
        """Requested `filing_index` is returned."""
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
        assert isinstance(asml22, Filing)
        assert asml22.filing_index == asml22_fxo

    @pytest.mark.sqlite
    def test_to_sqlite_filing_index(
            s, asml22en_response, tmp_path, monkeypatch):
        """Requested `filing_index` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        db_path = tmp_path / 'test_to_sqlite_filing_index.db'
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
        assert cur.fetchone() == (1,), 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_language(s, filter_language_response):
        """Filter `language` raises an `APIError`."""
        with pytest.raises(APIError, match='Bad filter value'):
            with pytest.warns(FilterNotSupportedWarning):
                _ = query.get_filings(
                    filters={
                        'language': 'fi'
                        },
                    sort=None,
                    max_size=1,
                    flags=GET_ONLY_FILINGS
                    )

    @pytest.mark.sqlite
    def test_to_sqlite_language(
        s, filter_language_response, tmp_path, monkeypatch):
        """Filter `language` raises an `APIError`."""
        monkeypatch.setattr(options, 'views', None)
        db_path = tmp_path / 'test_to_sqlite_language.db'
        with pytest.raises(APIError, match='Bad filter value'):
            with pytest.warns(FilterNotSupportedWarning):
                query.to_sqlite(
                    path=db_path,
                    update=False,
                    filters={
                        'language': 'fi'
                        },
                    sort=None,
                    max_size=1,
                    flags=GET_ONLY_FILINGS
                    )
        assert not os.access(db_path, os.F_OK), 'Database file is not created'

    def test_get_filings_last_end_date_str(s, filter_last_end_date_response):
        """Querying `last_end_date` as str returns filing(s)."""
        date_str = '2021-02-28'
        fs = query.get_filings(
            filters={
                'last_end_date': date_str
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        agrana20 = next(iter(fs), None)
        assert isinstance(agrana20, Filing)
        expected_date = date(*[int(pt) for pt in date_str.split('-')])
        assert agrana20.last_end_date == expected_date

    @pytest.mark.sqlite
    def test_to_sqlite_last_end_date_str(
            s, filter_last_end_date_response, tmp_path, monkeypatch):
        """Requested `last_end_date` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        date_str = '2021-02-28'
        db_path = tmp_path / 'test_to_sqlite_last_end_date.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'last_end_date': date_str
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE last_end_date = ?",
            (date_str,)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_last_end_date_obj(s, filter_last_end_date_response):
        """Querying `last_end_date` as date returns filing(s)."""
        date_obj = date(2021, 2, 28)
        fs = query.get_filings(
            filters={
                'last_end_date': date_obj
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        agrana20 = next(iter(fs), None)
        assert isinstance(agrana20, Filing)
        assert agrana20.last_end_date == date_obj

    @pytest.mark.sqlite
    def test_to_sqlite_last_end_date_obj(
            s, filter_last_end_date_response, tmp_path, monkeypatch):
        """Requested `last_end_date` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        date_obj = date(2021, 2, 28)
        db_path = tmp_path / 'test_to_sqlite_last_end_date.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'last_end_date': date_obj
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE last_end_date = ?",
            (date_obj.strftime('%Y-%m-%d'),)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_last_end_date_datetime(
            s, filter_last_end_date_dt_response):
        """Querying `last_end_date` as datetime raises ValueError."""
        dt_obj = datetime(2021, 2, 28, tzinfo=UTC)
        with pytest.raises(
            expected_exception=ValueError,
            match=r'Not possible to filter date field "\w+" by datetime'
            ):
            _ = query.get_filings(
                filters={
                    'last_end_date': dt_obj
                    },
                sort=None,
                max_size=1,
                flags=GET_ONLY_FILINGS
                )

    @pytest.mark.sqlite
    def test_to_sqlite_last_end_date_datetime(
            s, filter_last_end_date_dt_response, tmp_path, monkeypatch):
        """Requested `last_end_date` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        dt_obj = datetime(2021, 2, 28, tzinfo=UTC)
        db_path = tmp_path / 'test_to_sqlite_last_end_date.db'
        with pytest.raises(
            expected_exception=ValueError,
            match=r'Not possible to filter date field "\w+" by datetime'
            ):
            query.to_sqlite(
                path=db_path,
                update=False,
                filters={
                    'last_end_date': dt_obj
                    },
                sort=None,
                max_size=1,
                flags=GET_ONLY_FILINGS
                )

    @pytest.mark.xfail(
        reason=(
            'Filtering by "_count" attributes is not supported by the '
            'API.'
            ),
        raises=APIError)
    def test_get_filings_error_count(s, filter_error_count_response):
        """Filtering by `error_count` value 1 return one filing."""
        fs = query.get_filings(
            filters={
                'error_count': 1
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        filing = next(iter(fs), None)
        assert isinstance(filing, Filing)
        assert filing.error_count == 1

    @pytest.mark.xfail(
        reason=(
            'Filtering by "_count" attributes is not supported by the '
            'API.'
            ),
        raises=APIError)
    @pytest.mark.sqlite
    def test_to_sqlite_error_count(
            s, filter_error_count_response, tmp_path, monkeypatch):
        """Requested `error_count` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        db_path = tmp_path / 'test_to_sqlite_error_count.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'error_count': 1
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE error_count = ?",
            (1,)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_added_time_str(
            s, filter_added_time_response, monkeypatch):
        """Querying `added_time` as str returns filing(s)."""
        monkeypatch.setattr(options, 'time_accuracy', 'min')
        monkeypatch.setattr(options, 'utc_time', False)
        time_as_local = datetime(2021, 9, 23, 0, 0, tzinfo=UTC).astimezone()
        time_str = time_as_local.strftime('%Y-%m-%d %H:%M')
        fs = query.get_filings(
            filters={
                'added_time': time_str
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        vtbbank20 = next(iter(fs), None)
        assert isinstance(vtbbank20, Filing)
        assert vtbbank20.added_time == time_as_local

    @pytest.mark.sqlite
    def test_to_sqlite_added_time_str(
            s, filter_added_time_response, tmp_path, monkeypatch):
        """Requested `added_time` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        monkeypatch.setattr(options, 'time_accuracy', 'min')
        monkeypatch.setattr(options, 'utc_time', False)
        time_as_local = datetime(2021, 9, 23, 0, 0, tzinfo=UTC).astimezone()
        time_str = time_as_local.strftime('%Y-%m-%d %H:%M')
        db_path = tmp_path / 'test_to_sqlite_added_time_str.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'added_time': time_str
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE added_time = ?",
            (time_str,)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_added_time_datetime_utc(
            s, filter_added_time_response, monkeypatch):
        """Querying `added_time` as UTC datetime returns filing(s)."""
        monkeypatch.setattr(options, 'time_accuracy', 'min')
        monkeypatch.setattr(options, 'utc_time', False)
        dt_obj = datetime(2021, 9, 23, 0, 0, 0, tzinfo=UTC)
        fs = query.get_filings(
            filters={
                'added_time': dt_obj
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        vtbbank20 = next(iter(fs), None)
        assert isinstance(vtbbank20, Filing)
        dt_min_accurate = dt_obj.replace(second=0)
        assert vtbbank20.added_time == dt_min_accurate

    @pytest.mark.sqlite
    def test_to_sqlite_added_time_utc(
            s, filter_added_time_response, tmp_path, monkeypatch):
        """Requested `added_time` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        monkeypatch.setattr(options, 'time_accuracy', 'min')
        monkeypatch.setattr(options, 'utc_time', False)
        dt_obj = datetime(2021, 9, 23, 0, 0, 0, tzinfo=UTC)
        db_path = tmp_path / 'test_to_sqlite_added_time_utc.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'added_time': dt_obj
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        # Even though queried with UTC timezone datetime, date is saved
        # in local timezone because of `options.utc_time` = False
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE added_time = ?",
            (dt_obj.astimezone().strftime('%Y-%m-%d %H:%M'),)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_added_time_datetime_eest(
            s, filter_added_time_response, monkeypatch):
        """Querying `added_time` as EEST datetime returns filing(s)."""
        monkeypatch.setattr(options, 'time_accuracy', 'min')
        monkeypatch.setattr(options, 'utc_time', False)
        eest_tz = timezone(timedelta(hours=+3), 'EEST')
        dt_obj = datetime(2021, 9, 23, 3, 0, 0, tzinfo=eest_tz)
        fs = query.get_filings(
            filters={
                'added_time': dt_obj
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        vtbbank20 = next(iter(fs), None)
        assert isinstance(vtbbank20, Filing)
        dt_min_accurate = dt_obj.replace(second=0)
        assert vtbbank20.added_time == dt_min_accurate

    @pytest.mark.sqlite
    def test_to_sqlite_added_time_eest(
            s, filter_added_time_response, tmp_path, monkeypatch):
        """Requested `added_time` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        monkeypatch.setattr(options, 'time_accuracy', 'min')
        monkeypatch.setattr(options, 'utc_time', False)
        eest_tz = timezone(timedelta(hours=+3), 'EEST')
        dt_obj = datetime(2021, 9, 23, 3, 0, 0, tzinfo=eest_tz)
        db_path = tmp_path / 'test_to_sqlite_added_time_eest.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'added_time': dt_obj
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE added_time = ?",
            (dt_obj.astimezone().strftime('%Y-%m-%d %H:%M'),)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_added_time_date(s, filter_added_time_date_response):
        """Querying `added_time` as date raises ValueError."""
        date_obj = date(2021, 9, 23)
        with pytest.raises(
            expected_exception=ValueError,
            match=r'Not possible to filter datetime field "\w+" by date'
            ):
            _ = query.get_filings(
                filters={
                    'added_time': date_obj
                    },
                sort=None,
                max_size=1,
                flags=GET_ONLY_FILINGS
                )

    @pytest.mark.sqlite
    def test_to_sqlite_added_time_date(
            s, filter_added_time_date_response, tmp_path, monkeypatch):
        """Querying `added_time` as date for database raises ValueError."""
        monkeypatch.setattr(options, 'views', None)
        date_obj = date(2021, 9, 23)
        db_path = tmp_path / 'test_to_sqlite_added_time_date.db'
        with pytest.raises(
            expected_exception=ValueError,
            match=r'Not possible to filter datetime field "\w+" by date'
            ):
            query.to_sqlite(
                path=db_path,
                update=False,
                filters={
                    'added_time': date_obj
                    },
                sort=None,
                max_size=1,
                flags=GET_ONLY_FILINGS
                )
        assert not os.access(db_path, os.F_OK), 'Database file is not created'

    def test_get_filings_entity_api_id(s, filter_entity_api_id_response):
        """Querying `entity_api_id` raises APIError."""
        ent_id = 1/0
        with pytest.raises(APIError, match=r'Bad filter value'):
            _ = query.get_filings(
                filters={
                    'entity_api_id': ent_id
                    },
                sort=None,
                max_size=1,
                flags=GET_ONLY_FILINGS
                )

    @pytest.mark.xfail(
        reason=(
            'Filtering by "_url" attributes is not supported by the '
            'API.'
            ),
        raises=APIError)
    def test_get_filings_package_url(s, filter_package_url_response):
        """Filtering by `package_url` return one filing."""
        filter_url = (
            '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/'
            '2138001CNF45JP5XZK38-2022-12-31-EN.zip'
            )
        fs = query.get_filings(
            filters={
                'package_url': filter_url
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        kone22en = next(iter(fs), None)
        assert isinstance(kone22en, Filing)
        assert kone22en.package_url.endswith(filter_url)

    @pytest.mark.xfail(
        reason=(
            'Filtering by "_url" attributes is not supported by the '
            'API.'
            ),
        raises=APIError)
    @pytest.mark.sqlite
    def test_to_sqlite_package_url(
            s, filter_package_url_response, tmp_path, monkeypatch):
        """Requested `package_url` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        filter_url = (
            '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/'
            '2138001CNF45JP5XZK38-2022-12-31-EN.zip'
            )
        db_path = tmp_path / 'test_to_sqlite_package_url.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'package_url': filter_url
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE package_url LIKE '%?'",
            (1,)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_package_sha256(s, filter_package_sha256_response):
        """Querying `package_sha256` returns filing(s)."""
        filter_sha = (
            'e489a512976f55792c31026457e86c9176d258431f9ed645451caff9e4ef5f80')
        fs = query.get_filings(
            filters={
                'package_sha256': filter_sha
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        kone22en = next(iter(fs), None)
        assert isinstance(kone22en, Filing)
        assert kone22en.package_sha256 == filter_sha

    @pytest.mark.sqlite
    def test_to_sqlite_package_sha256(
            s, filter_package_sha256_response, tmp_path, monkeypatch):
        """Requested `package_sha256` is inserted into a database."""
        monkeypatch.setattr(options, 'views', None)
        filter_sha = (
            'e489a512976f55792c31026457e86c9176d258431f9ed645451caff9e4ef5f80')
        db_path = tmp_path / 'test_to_sqlite_package_sha256.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'package_sha256': filter_sha
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(db_path, os.F_OK), 'Database file is created'
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing WHERE package_sha256 = ?",
            (filter_sha,)
            )
        count_num = cur.fetchone()[0]
        assert count_num == 1, 'Inserted requested filing(s)'
        assert _sql_total_count_is(1, cur)

    def test_get_filings_2filters(s, finnish_jan22_response):
        """Filters `country` and `last_end_date` return 2 filings."""
        fs = query.get_filings(
            filters={
                'country': 'FI',
                'last_end_date': '2022-01-31'
                },
            sort=None,
            max_size=2,
            flags=GET_ONLY_FILINGS
            )
        assert len(fs) == 2, 'Two reports issued in Finland for Jan 2022.'
        fxo_set = {filing.filing_index for filing in fs}
        assert len(fxo_set) == 2, 'Filings are unique'

    @pytest.mark.sqlite
    def test_to_sqlite_2filters(
        s, finnish_jan22_response, tmp_path, monkeypatch):
        """Filters `country` and `last_end_date` insert 2 filings to db."""
        monkeypatch.setattr(options, 'views', None)
        db_path = tmp_path / 'test_to_sqlite_2filters.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'country': 'FI',
                'last_end_date': '2022-01-31'
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
            "WHERE country = ? AND last_end_date = ?",
            ('FI', '2022-01-31')
            )
        fxo_a = cur.fetchone()[0]
        fxo_b = cur.fetchone()[0]
        assert fxo_a != fxo_b, 'Filings are unique'
        assert cur.fetchone() is None, 'Two filings inserted'
        assert _sql_total_count_is(2, cur)

    def test_get_filings_2filters_date(s, finnish_jan22_response):
        """Filters `country` and `last_end_date` as date work."""
        fs = query.get_filings(
            filters={
                'country': 'FI',
                'last_end_date': date(2022, 1, 31)
                },
            sort=None,
            max_size=2,
            flags=GET_ONLY_FILINGS
            )
        assert len(fs) == 2, 'Two reports issued in Finland for Jan 2022.'
        fxo_set = {filing.filing_index for filing in fs}
        assert len(fxo_set) == 2, 'Filings are unique'

    @pytest.mark.sqlite
    def test_to_sqlite_2filters_date(
        s, finnish_jan22_response, tmp_path, monkeypatch):
        """Filters `country` and `last_end_date` as date insert to db."""
        monkeypatch.setattr(options, 'views', None)
        db_path = tmp_path / 'test_to_sqlite_2filters_date.db'
        query.to_sqlite(
            path=db_path,
            update=False,
            filters={
                'country': 'FI',
                'last_end_date': date(2022, 1, 31)
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
            "WHERE country = ? AND last_end_date = ?",
            ('FI', '2022-01-31')
            )
        fxo_a = cur.fetchone()[0]
        fxo_b = cur.fetchone()[0]
        assert fxo_a != fxo_b, 'Filings are unique'
        assert cur.fetchone() is None, 'Two filings inserted'
        assert _sql_total_count_is(2, cur)


class TestParam_filters_multifilters:
    """Test parameter `filters` using multifilters."""

    def test_get_filings_api_id(s, api_id_multifilter_response):
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

    def test_get_filings_country_only_first(s, country_multifilter_response):
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

    def test_get_filings_filing_index(
            s, filing_index_multifilter_response):
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

    def test_get_filings_reporting_date(s, reporting_date_multifilter_response):
        """APIError raised for filtering with `reporting_date`."""
        dates = '2020-12-31', '2021-12-31', '2022-12-31'
        with pytest.raises(APIError, match='Bad filter value'):
            with pytest.warns(FilterNotSupportedWarning):
                _ = query.get_filings(
                    filters={
                        'reporting_date': dates
                        },
                    sort=None,
                    max_size=3,
                    flags=GET_ONLY_FILINGS
                    )

    @pytest.mark.xfail(
        reason=(
            'Filtering by "_count" attributes is not supported by the '
            'API.'
            ),
        raises=APIError)
    def test_get_filings_inconsistency_count(
            s, inconsistency_count_multifilter_response):
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


    # to_sqlite
    # filing_page_iter


class TestParam_filters_short_dates:
    """Test parameter `filters` using date filters."""


    # to_sqlite
    # filing_page_iter


class TestParam_sort:
    """Test parameter `sort`."""

    def test_sort_oldest_finnish_str(s, oldest3_fi_response, monkeypatch):
        """Sort by `added_time` for filings from Finland."""
        monkeypatch.setattr(options, 'utc_time', True)
        fs = query.get_filings(
            filters={
                'country': 'FI'
                },
            sort='added_time',
            max_size=3,
            flags=GET_ONLY_FILINGS
            )
        date_max = datetime(2021, 5, 18, 0, 0, 1, tzinfo=UTC)
        for f in fs:
            assert f.added_time < date_max, 'Before 2021-05-18T00:00:01Z'

    def test_sort_oldest_finnish_list(s, oldest3_fi_response, monkeypatch):
        """Sort by `added_time` for filings from Finland."""
        monkeypatch.setattr(options, 'utc_time', True)
        fs = query.get_filings(
            filters={
                'country': 'FI'
                },
            sort=['added_time'],
            max_size=3,
            flags=GET_ONLY_FILINGS
            )
        date_max = datetime(2021, 5, 18, 0, 0, 1, tzinfo=UTC)
        for f in fs:
            assert f.added_time < date_max, 'Before 2021-05-18T00:00:01Z'

    def test_sort_two_fields(s, sort_two_fields_response):
        """
        Sort by `last_end_date`, `processed_time` for Finland filings.

        .. warning::

            This test is volatile regarding `mock_upgrade.py` runs.
            Systematically ancient (erraneous?) fact dates in new issued
            filings or introduction of older reports using other
            accounting principles/XBRL taxonomies may break it.
        """
        fs = query.get_filings(
            filters={
                'country': 'FI'
                },
            sort=['last_end_date', 'processed_time'],
            max_size=2,
            flags=GET_ONLY_FILINGS
            )
        assert len(fs) == 2, 'Two filings were requested'
        filing_indexes = {f.filing_index for f in fs}
        # TODO: Must be checked from full database output
        neste20en_fxo = '5493009GY1X8GQ66AM14-2020-12-31-ESEF-FI-0'
        assert neste20en_fxo in filing_indexes
        neste20fi_fxo = '5493009GY1X8GQ66AM14-2020-12-31-ESEF-FI-1'
        assert neste20fi_fxo in filing_indexes

    # to_sqlite
    # filing_page_iter


class TestParam_max_size:
    """Test parameter `max_size`."""

    # to_sqlite
    # filing_page_iter


class TestParam_flags:
    """Test parameter `flags`."""

    def test_get_filings_flag_only_filings(s, asml22en_response):
        """Test if function returns the filing according to `flags`."""
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
        assert asml22.entity is None, 'No entities'
        assert asml22.validation_messages is None, 'No messages'

    def test_get_filings_flag_entities(s, asml22en_entities_response):
        """Test if function returns the filing with `entity`."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        fs = query.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=GET_ENTITY
            )
        asml22 = next(iter(fs), None)
        assert asml22.validation_messages is None, 'No messages'
        assert isinstance(asml22.entity, Entity), 'Entity is available'
        assert asml22.entity.name == 'ASML Holding N.V.', 'Accessible'

    def test_get_filings_flag_vmessages(s, asml22en_vmessages_response):
        """Function returns the filing with `validation_messages`."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        fs = query.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=GET_VALIDATION_MESSAGES
            )
        asml22 = next(iter(fs), None)
        assert asml22.entity is None, 'No entity'
        vmsg = next(iter(asml22.validation_messages), None)
        assert isinstance(vmsg, ValidationMessage), 'Messages available'
        assert isinstance(vmsg.text, str), 'Messages accessible'

    def test_get_filings_flag_only_filings_and_entities(s, asml22en_response):
        """`GET_ONLY_FILINGS` is stronger than `GET_ENTITY`."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        fs = query.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS | GET_ENTITY
            )
        asml22 = next(iter(fs), None)
        assert asml22.entity is None, 'No entities'
        assert asml22.validation_messages is None, 'No messages'

    def test_get_filings_flag_entities_vmessages(s, asml22en_ent_vmsg_response):
        """Get entities and validation messages."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        fs = query.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=GET_ENTITY | GET_VALIDATION_MESSAGES
            )
        asml22 = next(iter(fs), None)
        assert isinstance(asml22.entity, Entity), 'Entity available'
        vmsg = next(iter(asml22.validation_messages), None)
        assert isinstance(vmsg, ValidationMessage), 'Messages available'
        assert isinstance(vmsg.text, str), 'Messages accessible'

    # to_sqlite
    # filing_page_iter


class TestParam_add_api_params:
    """Test parameter `add_api_params`."""

    def test_get_filings_override_max_size(s, asml22en_response):
        """`max_size` can be overridden with `add_api_params`."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        fs = query.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=10,
            flags=GET_ONLY_FILINGS,
            add_api_params={'page[size]': '1'}
            )
        assert len(fs) == 1, 'Parameter max_size is overridden to be 1'

    # to_sqlite
    # filing_page_iter


class TestParam_paging_single:
    """Test handling of filing pages from the API."""

    @pytest.mark.xfail(
        reason=(
            'Error in undelying API: redundant filings on pages. '
            'Filing with api_id "1" (Cloetta AB, 2021, en) and "2" '
            '(Cloetta AB, 2021, sv) is returned twice and as a result, '
            'a fouth page is requested to fulfil expected 5 filings.'
            ),
        raises=requests.ConnectionError
        )
    def test_filing_page_iter(s, multipage_xfail_response, monkeypatch):
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
