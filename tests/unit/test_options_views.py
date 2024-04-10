"""Define tests for `options.views`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import sqlite3

import pytest
import responses

import xbrl_filings_api as xf
from xbrl_filings_api.default_views import DEFAULT_VIEWS


@pytest.fixture(scope='module')
def get_asml22en_entities_filingset(urlmock):
    """Get FilingSet from mock response ``asml22en_entities``."""
    def _get_asml22en_entities_filingset():
        fs = None
        with responses.RequestsMock() as rsps:
            urlmock.apply(rsps, 'asml22en_entities')
            fs = xf.get_filings(
                filters={
                    'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
                    },
                sort=None,
                max_size=1,
                flags=xf.GET_ENTITY,
                add_api_params=None
                )
        return fs
    return _get_asml22en_entities_filingset


@pytest.mark.sqlite
def test_views_added(
        get_oldest3_fi_ent_vmessages_filingset, tmp_path, monkeypatch):
    """Test views are added when `options.views` is set."""
    monkeypatch.setattr(xf.options, 'views', DEFAULT_VIEWS)
    fs: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
    db_path = tmp_path / 'test_views_added.db'
    fs.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        'SELECT name FROM sqlite_schema WHERE type = ?', ('view',))
    existing_views = set(*zip(*cur.fetchall()))
    con.close()
    for dview in DEFAULT_VIEWS:
        assert dview.name in existing_views


@pytest.mark.sqlite
def test_views_not_added(
        get_oldest3_fi_ent_vmessages_filingset, tmp_path, monkeypatch):
    """Test views are not added when `options.views` is None."""
    monkeypatch.setattr(xf.options, 'views', None)
    fs: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
    db_path = tmp_path / 'test_views_not_added.db'
    fs.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        'SELECT name FROM sqlite_schema WHERE type = ?', ('view',))
    existing_views = set(*zip(*cur.fetchall()))
    con.close()
    assert existing_views == set()


@pytest.mark.sqlite
def test_require_entities_added(
        get_oldest3_fi_entities_filingset, tmp_path, monkeypatch):
    """Test view which requires entities is added properly."""
    monkeypatch.setattr(xf.options, 'views', DEFAULT_VIEWS)
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    db_path = tmp_path / 'test_require_entities_added.db'
    fs.to_sqlite(
        path=db_path,
        update=False,
        flags=xf.GET_ENTITY
        )
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        'SELECT name FROM sqlite_schema WHERE type = ?', ('view',))
    existing_views = set(*zip(*cur.fetchall()))
    con.close()
    assert 'ViewEnclosure' in existing_views


@pytest.mark.sqlite
def test_require_entities_not_added(
        get_oldest3_fi_filingset, tmp_path, monkeypatch):
    """
    Test view which requires entities is not added when no entities.
    """
    monkeypatch.setattr(xf.options, 'views', DEFAULT_VIEWS)
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    db_path = tmp_path / 'test_require_entities_not_added.db'
    fs.to_sqlite(
        path=db_path,
        update=False,
        flags=xf.GET_ONLY_FILINGS
        )
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        'SELECT name FROM sqlite_schema WHERE type = ?', ('view',))
    existing_views = set(*zip(*cur.fetchall()))
    con.close()
    assert 'ViewEnclosure' not in existing_views


@pytest.mark.sqlite
def test_add_with_same_name(
        get_oldest3_fi_ent_vmessages_filingset, tmp_path, monkeypatch):
    """Test with two views named ``ViewTest``."""
    sql = 'SELECT * FROM Filing'
    overlapping_list = [
        xf.SQLiteView(name='ViewTest', required_tables=(), sql=sql),
        xf.SQLiteView(name='ViewTest', required_tables=(), sql=sql),
        ]
    monkeypatch.setattr(xf.options, 'views', overlapping_list)
    fs: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
    db_path = tmp_path / 'test_add_with_same_name.db'
    with pytest.raises(
            ValueError,
            match=r'Multiple views in options\.views with name'):
        fs.to_sqlite(
            path=db_path,
            update=False,
            flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
            )
    assert not db_path.is_file()


@pytest.mark.sqlite
def test_views_retained_after_update(
        get_oldest3_fi_ent_vmessages_filingset,
        get_asml22en_entities_filingset, tmp_path, monkeypatch):
    """Test views are retained after update to the database."""
    monkeypatch.setattr(xf.options, 'views', DEFAULT_VIEWS)
    db_path = tmp_path / 'test_views_retained_after_update.db'
    flags = xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES

    fs_a: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
    fs_a.to_sqlite(
        path=db_path,
        update=False,
        flags=flags
        )
    fs_b: xf.FilingSet = get_asml22en_entities_filingset()
    fs_b.to_sqlite(
        path=db_path,
        update=True,
        flags=flags
        )

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        'SELECT name FROM sqlite_schema WHERE type = ?', ('view',))
    existing_views = set(*zip(*cur.fetchall()))
    con.close()
    for dview in DEFAULT_VIEWS:
        assert dview.name in existing_views
