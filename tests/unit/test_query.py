"""Define general tests for query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import sqlite3
from datetime import timezone

import pytest
import responses
from requests import JSONDecodeError

import xbrl_filings_api as xf
import xbrl_filings_api.exceptions as xf_exceptions

UTC = timezone.utc


def test_get_filings(asml22en_response):
    """Requested filing is returned."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=xf.GET_ONLY_FILINGS
        )
    asml22 = next(iter(fs), None)
    assert isinstance(asml22, xf.Filing), 'Filing is returned'


@pytest.mark.sqlite
def test_to_sqlite(asml22en_response, db_record_count, tmp_path, monkeypatch):
    """Requested filing is inserted into a database."""
    monkeypatch.setattr(xf.options, 'views', None)
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    db_path = tmp_path / 'test_to_sqlite.db'
    xf.to_sqlite(
        path=db_path,
        update=False,
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=xf.GET_ONLY_FILINGS
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM Filing WHERE filing_index = ?",
        (asml22_fxo,)
        )
    assert cur.fetchone() == (1,), 'Fetched record ends up in the database'
    assert db_record_count(cur) == 1
    con.close()


@pytest.mark.paging
def test_filing_page_iter(asml22en_response):
    """Requested filing is returned on a filing page."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    piter = xf.filing_page_iter(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=xf.GET_ONLY_FILINGS
        )
    page = next(piter, None)
    assert isinstance(page, xf.FilingsPage), 'First iteration returns a page'
    asml22 = next(iter(page.filing_list), None)
    assert isinstance(asml22, xf.Filing), 'Filing is returned on a page'


def test_get_filings_http_status_error():
    """Test raising when HTTP status is not 200."""
    with responses.RequestsMock() as rsps:
        rsps.get(
            url='https://filings.xbrl.org/api/filings',
            body='Testing.',
            status=404
            )
        with pytest.raises(xf_exceptions.HTTPStatusError) as exc_info:
            _ = xf.get_filings(
                filters=None,
                sort=None,
                max_size=100,
                flags=xf.GET_ONLY_FILINGS
                )
        exc = exc_info.value
        assert exc.status_code == 404
        assert exc.status_text == 'Not Found'
        assert exc.body == 'Testing.'


def test_get_filings_jsonapi_format_error_array():
    """Test raising when JSON document is an array."""
    with responses.RequestsMock() as rsps:
        rsps.get(
            url='https://filings.xbrl.org/api/filings',
            body='["test", "array"]',
            status=200
            )
        with pytest.raises(xf_exceptions.JSONAPIFormatError) as exc_info:
            _ = xf.get_filings(
                filters=None,
                sort=None,
                max_size=100,
                flags=xf.GET_ONLY_FILINGS
                )
        exc = exc_info.value
        assert exc.msg == 'JSON:API document is not a JSON object'


def test_get_filings_jsonapi_format_error_missing_keys():
    """Test raising when JSON document is missing the required keys."""
    with responses.RequestsMock() as rsps:
        rsps.get(
            url='https://filings.xbrl.org/api/filings',
            body='{"test": null}',
            status=200
            )
        with pytest.raises(xf_exceptions.JSONAPIFormatError) as exc_info:
            _ = xf.get_filings(
                filters=None,
                sort=None,
                max_size=100,
                flags=xf.GET_ONLY_FILINGS
                )
        exc = exc_info.value
        e_msg = (
            'JSON:API document does not have any of the required keys "data", '
            '"errors", "meta".'
            )
        assert exc.msg == e_msg


def test_get_filings_max_size_minus():
    """Test raising when max_size=-1."""
    with pytest.raises(
            ValueError,
            match=r'Parameter "max_size" may not be negative'):
        _ = xf.get_filings(
            filters=None,
            sort=None,
            max_size=-1,
            flags=xf.GET_ONLY_FILINGS
            )


def test_get_filings_bad_json(monkeypatch):
    """Test raising when API returns bad JSON."""
    monkeypatch.setattr(
        xf.options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
    with responses.RequestsMock() as rsps:
        rsps.get(
            url='https://filings.xbrl.org/api/filings',
            body='{"errors: null}'
            )
        with pytest.raises(JSONDecodeError):
            _ = xf.get_filings(
                filters=None,
                sort=None,
                max_size=100,
                flags=xf.GET_ONLY_FILINGS
                )


@pytest.mark.sqlite
def test_bad_options_time_accuracy(
        get_oldest3_fi_filingset, monkeypatch, tmp_path):
    """Test bad `options.time_accuracy`."""
    monkeypatch.setattr(xf.options, 'time_accuracy', 'bad_value')
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    path = tmp_path / 'test_bad_options_time_accuracy.db'
    with pytest.raises(
            ValueError,
            match=(r"options\.time_accuracy not in \{'day', 'min', 'sec', "
                   r"'max'\}")):
        fs.to_sqlite(
            path=path,
            update=False,
            flags=xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES
            )
