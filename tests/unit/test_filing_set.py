"""
Define tests for `FilingSet`.

Tests for downloading methods are in separate test module
`test_downloading`.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import sqlite3

import pytest

import xbrl_filings_api as xf


@pytest.fixture
def oldest3_fi_filingset(oldest3_fi_response):
    """Get FilingSet from mock URL response ``oldest3_fi``."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ONLY_FILINGS,
        add_api_params=None
        )


def test_attributes(oldest3_fi_filingset):
    """Test FilingSet attributes."""
    fs: xf.FilingSet = oldest3_fi_filingset
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert isinstance(fs.validation_messages, xf.ResourceCollection)
    assert isinstance(fs.columns, list)
    for col in fs.columns:
        assert isinstance(col, str)


def test_to_sqlite(oldest3_fi_filingset, db_record_count, tmp_path, monkeypatch):
    """Test method `to_sqlite`."""
    monkeypatch.setattr(xf.options, 'views', None)
    e_fxo_ids = {
        '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0',
        '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0',
        '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0',
        }
    fs: xf.FilingSet = oldest3_fi_filingset
    db_path = tmp_path / 'test_to_sqlite.db'
    fs.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file()
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT filing_index FROM Filing")
    saved_fxo_ids = {row[0] for row in cur.fetchall()}
    assert saved_fxo_ids == e_fxo_ids
    assert db_record_count(cur) == 3


# xf.FilingSet.to_sqlite
# xf.FilingSet.get_pandas_data
# xf.FilingSet._get_data_sets
# xf.FilingSet.columns
