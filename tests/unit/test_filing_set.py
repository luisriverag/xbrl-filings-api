"""
Define tests for `FilingSet`.

Tests for downloading methods are in separate test module
``test_downloading`` and for the method get_pandas_data in module
``test_pandas_data``.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import sqlite3
from collections.abc import Collection

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


@pytest.mark.sqlite
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


def test_get_data_sets_only_filings(oldest3_fi_filingset):
    """Test method `_get_data_sets` when set has only filings."""
    fs: xf.FilingSet = oldest3_fi_filingset
    flags = (xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing'}
    assert flags == xf.GET_ONLY_FILINGS
    assert len(data_objs['Filing']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)


def test_get_data_sets_entities(oldest3_fi_entities_response):
    """Test method `_get_data_sets` when set has entities."""
    fs: xf.FilingSet = xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ENTITY,
        add_api_params=None
        )
    flags = (xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing', 'Entity'}
    assert flags == xf.GET_ENTITY
    assert len(data_objs['Filing']) == 3
    assert len(data_objs['Entity']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)
    for ent in data_objs['Entity']:
        assert isinstance(ent, xf.Entity)


def test_get_data_sets_entities_out(oldest3_fi_entities_response):
    """Test method `_get_data_sets` when set has entities but leaves them out."""
    fs: xf.FilingSet = xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ENTITY,
        add_api_params=None
        )
    flags = xf.GET_ONLY_FILINGS
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing'}
    assert flags == xf.GET_ONLY_FILINGS
    assert len(data_objs['Filing']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)


def test_get_data_sets_vmessages(oldest3_fi_vmessages_response):
    """Test method `_get_data_sets` when set has validation messages."""
    fs: xf.FilingSet = xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_VALIDATION_MESSAGES,
        add_api_params=None
        )
    flags = (xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing', 'ValidationMessage'}
    assert flags == xf.GET_VALIDATION_MESSAGES
    assert len(data_objs['Filing']) == 3
    assert len(data_objs['ValidationMessage']) > 0
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)
    for vmsg in data_objs['ValidationMessage']:
        assert isinstance(vmsg, xf.ValidationMessage)


def test_get_data_sets_entities_vmessages(oldest3_fi_ent_vmessages_response):
    """Test method `_get_data_sets` when set has entities and validation messages."""
    fs: xf.FilingSet = xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES),
        add_api_params=None
        )
    flags = (xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing', 'Entity', 'ValidationMessage'}
    assert flags == (xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
    assert len(data_objs['Filing']) == 3
    assert len(data_objs['Entity']) == 3
    assert len(data_objs['ValidationMessage']) > 0
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)
    for ent in data_objs['Entity']:
        assert isinstance(ent, xf.Entity)
    for vmsg in data_objs['ValidationMessage']:
        assert isinstance(vmsg, xf.ValidationMessage)


def test_get_data_sets_entities_vmessages_ent_out(oldest3_fi_ent_vmessages_response):
    """Test method `_get_data_sets` when set has entities and validation messages leaving entities."""
    fs: xf.FilingSet = xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES),
        add_api_params=None
        )
    flags = xf.GET_VALIDATION_MESSAGES
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing', 'ValidationMessage'}
    assert flags == xf.GET_VALIDATION_MESSAGES
    assert len(data_objs['Filing']) == 3
    assert len(data_objs['ValidationMessage']) > 0
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)
    for vmsg in data_objs['ValidationMessage']:
        assert isinstance(vmsg, xf.ValidationMessage)


def test_get_data_sets_entities_vmessages_all_out(oldest3_fi_ent_vmessages_response):
    """Test method `_get_data_sets` when set has entities and validation messages but selects only filings."""
    fs: xf.FilingSet = xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES),
        add_api_params=None
        )
    flags = xf.GET_ONLY_FILINGS
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing'}
    assert flags == xf.GET_ONLY_FILINGS
    assert len(data_objs['Filing']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)


def test_columns_property(oldest3_fi_filingset):
    fs: xf.FilingSet = oldest3_fi_filingset
    assert isinstance(fs.columns, list)
    assert len(fs.columns) > 0
    for col in fs.columns:
        assert isinstance(col, str)
    assert 'api_id' in fs.columns
