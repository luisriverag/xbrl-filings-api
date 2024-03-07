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
    """FilingSet from mock response ``oldest3_fi``."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ONLY_FILINGS,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_entities_filingset(oldest3_fi_entities_response):
    """FilingSet from mock response ``oldest3_fi_entities`` with entities."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ENTITY,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_vmessages_filingset(oldest3_fi_vmessages_response):
    """FilingSet from mock response ``oldest3_fi_vmessages`` with validation messages."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_VALIDATION_MESSAGES,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_ent_vmessages_filingset(oldest3_fi_ent_vmessages_response):
    """FilingSet from mock response ``oldest3_fi_ent_vmessages`` with entities and validation messages."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES),
        add_api_params=None
        )


@pytest.fixture
def asml22en_filingset(asml22en_response):
    """FilingSet from mock response ``asml22en``."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    return xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=xf.GET_ONLY_FILINGS
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


@pytest.mark.sqlite
def test_to_sqlite_update_same_add_entities(
        oldest3_fi_filingset, oldest3_fi_entities_filingset, db_record_count,
        tmp_path, monkeypatch):
    """Test method `to_sqlite` with update=True updating same records, adding Entity."""
    monkeypatch.setattr(xf.options, 'views', None)
    e_fxo_ids = {
        '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0',
        '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0',
        '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0',
        }
    db_path = tmp_path / 'test_to_sqlite_update_same_add_entities.db'

    fs_a: xf.FilingSet = oldest3_fi_filingset
    fs_a.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file()
    con_a = sqlite3.connect(db_path)
    cur_a = con_a.cursor()
    assert db_record_count(cur_a) == 3
    with pytest.raises(sqlite3.OperationalError, match='no such column'):
        cur_a.execute("SELECT entity_api_id FROM Filing")
    cur_a.execute("SELECT api_id, filing_index FROM Filing")
    resultzip = zip(*cur_a.fetchall())
    before_api_ids = set(next(resultzip))
    before_filing_indexes = set(next(resultzip))
    assert before_filing_indexes == e_fxo_ids
    with pytest.raises(sqlite3.OperationalError, match='no such table'):
        cur_a.execute("SELECT * FROM Entity")
    con_a.close()

    fs_b: xf.FilingSet = oldest3_fi_entities_filingset
    fs_b.to_sqlite(
        path=db_path,
        update=True,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file(), "Update won't delete database file"
    con_b = sqlite3.connect(db_path)
    cur_b = con_b.cursor()
    assert db_record_count(cur_b) == 3
    cur_b.execute("SELECT api_id, entity_api_id, filing_index FROM Filing")
    resultzip = zip(*cur_b.fetchall())
    after_api_ids = set(next(resultzip))
    after_filing_entity_api_ids = set(next(resultzip))
    after_filing_indexes = set(next(resultzip))
    assert None not in after_filing_entity_api_ids, 'Entity foreign keys added'
    assert after_filing_indexes == e_fxo_ids
    cur_b.execute("SELECT api_id FROM Entity")
    after_entity_api_ids = set(*zip(*cur_b.fetchall()))
    assert None not in after_entity_api_ids, 'Entities added'
    assert after_filing_entity_api_ids == after_entity_api_ids, (
        'Foreign keys match primary keys on Entity')
    con_b.close()
    assert before_api_ids == after_api_ids


@pytest.mark.sqlite
def test_to_sqlite_update_same_add_vmessages(
        oldest3_fi_filingset, oldest3_fi_vmessages_filingset, db_record_count,
        tmp_path, monkeypatch):
    """Test method `to_sqlite` with update=True updating same records, adding ValidationMessage."""
    monkeypatch.setattr(xf.options, 'views', None)
    e_fxo_ids = {
        '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0',
        '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0',
        '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0',
        }
    db_path = tmp_path / 'test_to_sqlite_update_same_add_vmessages.db'

    fs_a: xf.FilingSet = oldest3_fi_filingset
    fs_a.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file()
    con_a = sqlite3.connect(db_path)
    cur_a = con_a.cursor()
    assert db_record_count(cur_a) == 3
    cur_a.execute("SELECT api_id, filing_index FROM Filing")
    resultzip = zip(*cur_a.fetchall())
    before_api_ids = set(next(resultzip))
    before_filing_indexes = set(next(resultzip))
    assert before_filing_indexes == e_fxo_ids
    with pytest.raises(sqlite3.OperationalError, match='no such table'):
        cur_a.execute("SELECT * FROM ValidationMessage")
    con_a.close()

    fs_b: xf.FilingSet = oldest3_fi_vmessages_filingset
    fs_b.to_sqlite(
        path=db_path,
        update=True,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file(), "Update won't delete database file"
    con_b = sqlite3.connect(db_path)
    cur_b = con_b.cursor()
    assert db_record_count(cur_b) == 3
    cur_b.execute("SELECT api_id, filing_index FROM Filing")
    resultzip = zip(*cur_b.fetchall())
    after_api_ids = set(next(resultzip))
    after_filing_indexes = set(next(resultzip))
    assert after_filing_indexes == e_fxo_ids
    cur_b.execute("SELECT api_id, filing_api_id FROM ValidationMessage")
    resultzip = zip(*cur_b.fetchall())
    after_vmessage_api_ids = set(next(resultzip))
    after_vmessage_filing_api_ids = set(next(resultzip))
    assert None not in after_vmessage_api_ids, 'Validation messages added'
    assert after_vmessage_filing_api_ids == after_api_ids, (
        'Foreign keys match primary keys on ValidationMessage')
    con_b.close()
    assert before_api_ids == after_api_ids


@pytest.mark.sqlite
def test_to_sqlite_update_more(
        oldest3_fi_filingset, asml22en_filingset, db_record_count,
        tmp_path, monkeypatch):
    """Test method `to_sqlite` with update=True adding more records."""
    monkeypatch.setattr(xf.options, 'views', None)
    e_before_fxo_ids = {
        '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0',
        '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0',
        '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0',
        }
    e_added_fxo_id = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    db_path = tmp_path / 'test_to_sqlite_update_more.db'

    fs_a: xf.FilingSet = oldest3_fi_filingset
    fs_a.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file()
    con_a = sqlite3.connect(db_path)
    cur_a = con_a.cursor()
    assert db_record_count(cur_a) == 3
    cur_a.execute("SELECT api_id, filing_index FROM Filing")
    resultzip = zip(*cur_a.fetchall())
    before_api_ids = set(next(resultzip))
    before_filing_indexes = set(next(resultzip))
    assert before_filing_indexes == e_before_fxo_ids
    con_a.close()

    fs_b: xf.FilingSet = asml22en_filingset
    fs_b.to_sqlite(
        path=db_path,
        update=True,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file(), "Update won't delete database file"
    con_b = sqlite3.connect(db_path)
    cur_b = con_b.cursor()
    assert db_record_count(cur_b) == 4
    cur_b.execute("SELECT api_id, filing_index FROM Filing")
    resultzip = zip(*cur_b.fetchall())
    after_api_ids = set(next(resultzip))
    after_filing_indexes = set(next(resultzip))
    assert after_filing_indexes == {*e_before_fxo_ids, e_added_fxo_id}
    con_b.close()
    for retained_api_id in before_api_ids:
        assert retained_api_id in after_api_ids


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


def test_get_data_sets_entities(oldest3_fi_entities_filingset):
    """Test method `_get_data_sets` when set has entities."""
    fs: xf.FilingSet = oldest3_fi_entities_filingset
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


def test_get_data_sets_entities_out(oldest3_fi_entities_filingset):
    """Test method `_get_data_sets` when set has entities but leaves them out."""
    fs: xf.FilingSet = oldest3_fi_entities_filingset
    flags = xf.GET_ONLY_FILINGS
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing'}
    assert flags == xf.GET_ONLY_FILINGS
    assert len(data_objs['Filing']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)


def test_get_data_sets_vmessages(oldest3_fi_vmessages_filingset):
    """Test method `_get_data_sets` when set has validation messages."""
    fs: xf.FilingSet = oldest3_fi_vmessages_filingset
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


def test_get_data_sets_entities_vmessages(oldest3_fi_ent_vmessages_filingset):
    """Test method `_get_data_sets` when set has entities and validation messages."""
    fs: xf.FilingSet = oldest3_fi_ent_vmessages_filingset
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


def test_get_data_sets_entities_vmessages_ent_out(oldest3_fi_ent_vmessages_filingset):
    """Test method `_get_data_sets` when set has entities and validation messages leaving entities."""
    fs: xf.FilingSet = oldest3_fi_ent_vmessages_filingset
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


def test_get_data_sets_entities_vmessages_all_out(oldest3_fi_ent_vmessages_filingset):
    """Test method `_get_data_sets` when set has entities and validation messages but selects only filings."""
    fs: xf.FilingSet = oldest3_fi_ent_vmessages_filingset
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
