"""Define tests for `default_views`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import sqlite3

import pytest

import xbrl_filings_api as xf
from xbrl_filings_api.default_views import DEFAULT_VIEWS


@pytest.mark.sqlite
def test_views_added(oldest3_fi_ent_vmessages_filingset, tmp_path, monkeypatch):
    """Test views are added when `options.views` is set."""
    monkeypatch.setattr(xf.options, 'views', DEFAULT_VIEWS)
    fs: xf.FilingSet = oldest3_fi_ent_vmessages_filingset
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
def test_views_not_added(oldest3_fi_ent_vmessages_filingset, tmp_path, monkeypatch):
    """Test views are not added when `options.views` is None."""
    monkeypatch.setattr(xf.options, 'views', None)
    fs: xf.FilingSet = oldest3_fi_ent_vmessages_filingset
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
def test_require_entities_added(oldest3_fi_entities_filingset, tmp_path, monkeypatch):
    """Test view which requires entities is added properly."""
    monkeypatch.setattr(xf.options, 'views', DEFAULT_VIEWS)
    fs: xf.FilingSet = oldest3_fi_entities_filingset
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
    assert 'ViewFiling' in existing_views


@pytest.mark.sqlite
def test_require_entities_not_added(oldest3_fi_filingset, tmp_path, monkeypatch):
    """Test view which requires entities is not added when no entities."""
    monkeypatch.setattr(xf.options, 'views', DEFAULT_VIEWS)
    fs: xf.FilingSet = oldest3_fi_filingset
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
    assert 'ViewFiling' not in existing_views


# next(v for v in xf.default_views.DEFAULT_VIEWS if v.name == 'ViewNumericInconsistency')
# next(v for v in xf.default_views.DEFAULT_VIEWS if v.name == 'ViewFiling')
# next(v for v in xf.default_views.DEFAULT_VIEWS if v.name == 'ViewTime')
