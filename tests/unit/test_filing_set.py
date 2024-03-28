"""
Define tests for `FilingSet`.

Tests for downloading methods are in separate test module
``test_downloading`` and for the method get_pandas_data in module
``test_pandas_data``.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import copy
import sqlite3
from collections.abc import Collection
from datetime import date

import pytest
import responses

import xbrl_filings_api as xf


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


@pytest.fixture
def ageas21_22_filingset(urlmock):
    ageas21_22_ids = '3314', '3316', '3315', '5139', '5140', '5141'
    fs = None
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'ageas21_22')
        fs = xf.get_filings(
            filters={'api_id': ageas21_22_ids},
            sort=None,
            max_size=6,
            flags=xf.GET_ENTITY
            )
    return fs


@pytest.fixture
def applus20_21_filingset(urlmock):
    applus20_21_ids = '1733', '1734'
    fs = None
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'applus20_21')
        fs = xf.get_filings(
            filters={'api_id': applus20_21_ids},
            sort=None,
            max_size=2,
            flags=xf.GET_ENTITY
            )
    return fs


def test_attributes(get_oldest3_fi_filingset):
    """Test FilingSet attributes."""
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert isinstance(fs.validation_messages, xf.ResourceCollection)
    assert isinstance(fs.columns, list)
    for col in fs.columns:
        assert isinstance(col, str)


@pytest.mark.sqlite
def test_to_sqlite(get_oldest3_fi_filingset, db_record_count, tmp_path, monkeypatch):
    """Test method `to_sqlite`."""
    monkeypatch.setattr(xf.options, 'views', None)
    e_fxo_ids = {
        '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0',
        '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0',
        '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0',
        }
    fs: xf.FilingSet = get_oldest3_fi_filingset()
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
    con.close()


@pytest.mark.sqlite
def test_to_sqlite_update_same_add_entities(
        get_oldest3_fi_filingset, get_oldest3_fi_entities_filingset, db_record_count,
        tmp_path, monkeypatch):
    """Test method `to_sqlite` with update=True updating same records, adding Entity."""
    monkeypatch.setattr(xf.options, 'views', None)
    e_fxo_ids = {
        '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0',
        '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0',
        '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0',
        }
    db_path = tmp_path / 'test_to_sqlite_update_same_add_entities.db'

    fs_a: xf.FilingSet = get_oldest3_fi_filingset()
    fs_a.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file()
    con_a = sqlite3.connect(db_path)
    cur_a = con_a.cursor()
    assert db_record_count(cur_a) == 3
    with pytest.raises(sqlite3.OperationalError, match=r'no such column'):
        cur_a.execute("SELECT entity_api_id FROM Filing")
    cur_a.execute("SELECT api_id, filing_index FROM Filing")
    resultzip = zip(*cur_a.fetchall())
    before_api_ids = set(next(resultzip))
    before_filing_indexes = set(next(resultzip))
    assert before_filing_indexes == e_fxo_ids
    with pytest.raises(sqlite3.OperationalError, match=r'no such table'):
        cur_a.execute("SELECT * FROM Entity")
    con_a.close()

    fs_b: xf.FilingSet = get_oldest3_fi_entities_filingset()
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
        get_oldest3_fi_filingset, get_oldest3_fi_vmessages_filingset, db_record_count,
        tmp_path, monkeypatch):
    """Test method `to_sqlite` with update=True updating same records, adding ValidationMessage."""
    monkeypatch.setattr(xf.options, 'views', None)
    e_fxo_ids = {
        '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0',
        '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0',
        '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0',
        }
    db_path = tmp_path / 'test_to_sqlite_update_same_add_vmessages.db'

    fs_a: xf.FilingSet = get_oldest3_fi_filingset()
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
    with pytest.raises(sqlite3.OperationalError, match=r'no such table'):
        cur_a.execute("SELECT * FROM ValidationMessage")
    con_a.close()

    fs_b: xf.FilingSet = get_oldest3_fi_vmessages_filingset()
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
        get_oldest3_fi_filingset, asml22en_filingset, db_record_count,
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

    fs_a: xf.FilingSet = get_oldest3_fi_filingset()
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


@pytest.mark.sqlite
def test_to_sqlite_update_more_but_false(
        get_oldest3_fi_filingset, asml22en_filingset, tmp_path, monkeypatch):
    """Test method `to_sqlite` trying to update existing database but update=False."""
    monkeypatch.setattr(xf.options, 'views', None)
    db_path = tmp_path / 'test_to_sqlite_update_more_but_false.db'

    fs_a: xf.FilingSet = get_oldest3_fi_filingset()
    fs_a.to_sqlite(
        path=db_path,
        update=False,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
        )
    assert db_path.is_file()
    stbef = db_path.stat()
    edit_time_before = stbef.st_mtime, stbef.st_ctime

    fs_b: xf.FilingSet = asml22en_filingset
    with pytest.raises(FileExistsError):
        fs_b.to_sqlite(
            path=db_path,
            update=False,
            flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
            )
    assert db_path.is_file(), "Failed update won't delete database file"
    staft = db_path.stat()
    edit_time_after = staft.st_mtime, staft.st_ctime
    assert edit_time_before == edit_time_after, "Failed update won't edit file"


@pytest.mark.sqlite
def test_to_sqlite_update_no_tables(
    asml22en_filingset, tmp_path, monkeypatch):
    """Test method `to_sqlite` trying to update database without expected tables."""
    monkeypatch.setattr(xf.options, 'views', None)
    db_path = tmp_path / 'test_to_sqlite_update_no_tables.db'

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript(
        'CREATE TABLE Animal ('
        'id TEXT PRIMARY KEY NOT NULL, iscute INTEGER NOT NULL'
        ') WITHOUT ROWID;'
        )
    con.commit()
    cur.executemany(
        'INSERT INTO Animal (id, iscute) VALUES (?, ?)',
        [('wombat', 1), ('vampire bat', 0), ('cat', 1)])
    con.commit()
    con.close()
    stbef = db_path.stat()
    edit_time_before = stbef.st_mtime, stbef.st_ctime

    fs_b: xf.FilingSet = asml22en_filingset
    with pytest.raises(xf.DatabaseSchemaUnmatchError) as exc_info:
        fs_b.to_sqlite(
            path=db_path,
            update=True,
            flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
            )
    err = exc_info.value
    assert err.path == str(db_path)
    assert str(err) == f'path={str(db_path)!r}'

    assert db_path.is_file(), "Failed update won't delete database file"
    staft = db_path.stat()
    edit_time_after = staft.st_mtime, staft.st_ctime
    assert edit_time_before == edit_time_after, "Failed update won't edit file"


@pytest.mark.sqlite
def test_to_sqlite_update_no_api_id(
    asml22en_filingset, tmp_path, monkeypatch):
    """Test method `to_sqlite` trying to update database whose table has no api_id."""
    monkeypatch.setattr(xf.options, 'views', None)
    db_path = tmp_path / 'test_to_sqlite_update_no_api_id.db'

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript(
        'CREATE TABLE Filing ('
        'filing_index TEXT PRIMARY KEY NOT NULL, country TEXT NOT NULL'
        ') WITHOUT ROWID;'
        )
    con.commit()
    cur.executemany(
        'INSERT INTO Filing (filing_index, country) VALUES (?, ?)',
        [
            ('743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0', 'FI'),
            ('549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0', 'FI')
        ])
    con.commit()
    con.close()
    stbef = db_path.stat()
    edit_time_before = stbef.st_mtime, stbef.st_ctime

    fs_b: xf.FilingSet = asml22en_filingset
    with pytest.raises(xf.DatabaseSchemaUnmatchError) as exc_info:
        fs_b.to_sqlite(
            path=db_path,
            update=True,
            flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
            )
    err = exc_info.value
    assert err.path == str(db_path)
    assert str(err) == f'path={str(db_path)!r}'

    assert db_path.is_file(), "Failed update won't delete database file"
    staft = db_path.stat()
    edit_time_after = staft.st_mtime, staft.st_ctime
    assert edit_time_before == edit_time_after, "Failed update won't edit file"


@pytest.mark.sqlite
def test_to_sqlite_path_reserved(
        get_oldest3_fi_filingset, tmp_path, monkeypatch):
    """Test method `to_sqlite` but assigned path is a folder."""
    monkeypatch.setattr(xf.options, 'views', None)
    reserved_path = tmp_path / 'test_to_sqlite_path_reserved'
    reserved_path.mkdir()

    fs_a: xf.FilingSet = get_oldest3_fi_filingset()
    with pytest.raises(
            sqlite3.OperationalError, match=r'unable to open database file'):
        fs_a.to_sqlite(
            path=reserved_path,
            update=False,
            flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
            )
    assert reserved_path.is_dir()


def test_get_data_sets_only_filings(get_oldest3_fi_filingset):
    """Test method `_get_data_sets` when set has only filings."""
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    flags = (xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES)
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing'}
    assert flags == xf.GET_ONLY_FILINGS
    assert len(data_objs['Filing']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)


def test_get_data_sets_entities(get_oldest3_fi_entities_filingset):
    """Test method `_get_data_sets` when set has entities."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
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


def test_get_data_sets_entities_out(get_oldest3_fi_entities_filingset):
    """Test method `_get_data_sets` when set has entities but leaves them out."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    flags = xf.GET_ONLY_FILINGS
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing'}
    assert flags == xf.GET_ONLY_FILINGS
    assert len(data_objs['Filing']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)


def test_get_data_sets_vmessages(get_oldest3_fi_vmessages_filingset):
    """Test method `_get_data_sets` when set has validation messages."""
    fs: xf.FilingSet = get_oldest3_fi_vmessages_filingset()
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


def test_get_data_sets_entities_vmessages(get_oldest3_fi_ent_vmessages_filingset):
    """Test method `_get_data_sets` when set has entities and validation messages."""
    fs: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
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


def test_get_data_sets_entities_vmessages_ent_out(get_oldest3_fi_ent_vmessages_filingset):
    """Test method `_get_data_sets` when set has entities and validation messages leaving entities."""
    fs: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
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


def test_get_data_sets_entities_vmessages_all_out(get_oldest3_fi_ent_vmessages_filingset):
    """Test method `_get_data_sets` when set has entities and validation messages but selects only filings."""
    fs: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
    flags = xf.GET_ONLY_FILINGS
    data_objs, flags = fs._get_data_sets(flags)
    assert set(data_objs) == {'Filing'}
    assert flags == xf.GET_ONLY_FILINGS
    assert len(data_objs['Filing']) == 3
    for filing in data_objs['Filing']:
        assert isinstance(filing, xf.Filing)


def test_columns_property(get_oldest3_fi_filingset):
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    assert isinstance(fs.columns, list)
    assert len(fs.columns) > 0
    for col in fs.columns:
        assert isinstance(col, str)
    assert 'api_id' in fs.columns


def test_repr(get_oldest3_fi_filingset):
    """Test `__repr__` of FilingSet."""
    e_repr = 'FilingSet(len(self)=3)'
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    assert repr(fs) == e_repr


def test_repr_ent_vmessages(get_oldest3_fi_ent_vmessages_filingset):
    """Test `__repr__` of FilingSet."""
    e_repr = (
        'FilingSet(len(self)=3, len(entities)=3, len(validation_messages)=45)')
    fs: xf.FilingSet = get_oldest3_fi_ent_vmessages_filingset()
    assert repr(fs) == e_repr


def test_contains_is_true_diff_identities(get_oldest3_fi_filingset):
    """Test `in` operator evaluates to True if filing is same but identity different."""
    fs_a: xf.FilingSet = get_oldest3_fi_filingset()
    fs_b: xf.FilingSet = get_oldest3_fi_filingset()
    filing_a = next(iter(fs_a))
    # Determined by type and api_id
    assert filing_a in fs_b


def test_contains_is_false_wrong_type(get_oldest3_fi_entities_filingset):
    """Test `in` operator evaluates to False when wrong type."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    filing = next(iter(fs))
    assert filing.entity not in fs


def test_contains_is_false_wrong_api_id(get_oldest3_fi_entities_filingset):
    """Test `in` operator evaluates to False when wrong api_id."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    filing = next(iter(fs))
    filing_copy = copy.deepcopy(filing)
    filing_copy.api_id = 'abc'
    assert filing_copy not in fs


def test_pop_duplicates_raises_no_entities(multifilter_api_id_response):
    """Test pop_duplicates method raises ValueError when no entities."""
    shell21_22_gb_nl_ids = '1134', '1135', '4496', '4529'
    fs = xf.get_filings(
        filters={'api_id': shell21_22_gb_nl_ids},
        sort=None,
        max_size=4,
        flags=xf.GET_ONLY_FILINGS
        )
    fs_before = set(fs)
    with pytest.raises(
            ValueError, match=r'Entities must be available on the FilingSet'):
        _ = fs.pop_duplicates(
            languages=['en'],
            use_reporting_date=False,
            all_markets=False
            )
    assert fs_before == set(fs)


def test_pop_duplicates_two_markets_all_markets_false(multifilter_api_id_entities_response):
    """Test pop_duplicates method with two market enclosure, all_markets=False."""
    shell21_22_gb_nl_ids = '1134', '1135', '4496', '4529'
    fs = xf.get_filings(
        filters={'api_id': shell21_22_gb_nl_ids},
        sort=None,
        max_size=4,
        flags=xf.GET_ENTITY
        )
    popped = fs.pop_duplicates(
        languages=['en'],
        use_reporting_date=False,
        all_markets=False
        )
    assert isinstance(fs, xf.FilingSet)
    assert len(fs) == 2
    for filing in fs:
        assert filing.language == 'en'
        assert filing.country == 'NL'
    assert isinstance(popped, xf.FilingSet)
    assert len(popped) == 2
    for filing in popped:
        assert filing.language is None
        assert filing.country == 'GB'


def test_pop_duplicates_two_markets_all_markets_true(multifilter_api_id_entities_response):
    """Test pop_duplicates method with two market enclosure, all_markets=True."""
    shell21_22_gb_nl_ids = '1134', '1135', '4496', '4529'
    fs = xf.get_filings(
        filters={'api_id': shell21_22_gb_nl_ids},
        sort=None,
        max_size=4,
        flags=xf.GET_ENTITY
        )
    popped = fs.pop_duplicates(
        languages=['en'],
        use_reporting_date=False,
        all_markets=True
        )
    assert isinstance(fs, xf.FilingSet)
    assert len(fs) == 4
    assert isinstance(popped, xf.FilingSet)
    assert len(popped) == 0


@pytest.mark.parametrize('languages,match_lang,pop_lang', [
    (['en'], 'en', ('fr', 'nl')),
    (['fi', 'nl'], 'nl', ('fr', 'en')),
    ([None, 'fr', 'nl'], 'fr', ('nl', 'en')),
    ])
def test_pop_duplicates_3languages_2enclosures_match_language(
        languages, match_lang, pop_lang, ageas21_22_filingset):
    """Test pop_duplicates method with 3 languages, 2 enclosures."""
    fs: xf.FilingSet = ageas21_22_filingset
    popped = fs.pop_duplicates(
        languages=languages,
        use_reporting_date=False,
        all_markets=False
        )
    assert isinstance(fs, xf.FilingSet)
    assert len(fs) == 2
    e_retained_dates = [date(2021, 12, 31), date(2022, 12, 31)]
    for filing in fs:
        assert filing.language == match_lang
        e_retained_dates.remove(filing.last_end_date)

    assert isinstance(popped, xf.FilingSet)
    assert len(popped) == 4
    e_popped_dates = [
        date(2021, 12, 31), date(2021, 12, 31), date(2022, 12, 31),
        date(2022, 12, 31)
        ]
    for filing in popped:
        assert filing.language in pop_lang
        e_popped_dates.remove(filing.last_end_date)


@pytest.mark.parametrize('languages', [None, [None], ['fi', 'sv']])
def test_pop_duplicates_3languages_2enclosures_max_filing_index(
        languages, ageas21_22_filingset):
    """Test pop_duplicates method with 3 languages, 2 enclosures, fallback max filing_index."""
    fs: xf.FilingSet = ageas21_22_filingset
    popped = fs.pop_duplicates(
        languages=languages,
        use_reporting_date=False,
        all_markets=False
        )
    assert isinstance(fs, xf.FilingSet)
    assert len(fs) == 2
    e_retained_dates = [date(2021, 12, 31), date(2022, 12, 31)]
    e_max_filing_indexes = (
        '5493005DJBML6LY3RV36-2021-12-31-ESEF-BE-2',
        '5493005DJBML6LY3RV36-2022-12-31-ESEF-BE-2'
        )
    for filing in fs:
        assert filing.filing_index in e_max_filing_indexes
        e_retained_dates.remove(filing.last_end_date)

    assert isinstance(popped, xf.FilingSet)
    assert len(popped) == 4
    e_popped_dates = [
        date(2021, 12, 31), date(2021, 12, 31), date(2022, 12, 31),
        date(2022, 12, 31)
        ]
    for filing in popped:
        assert filing.filing_index not in e_max_filing_indexes
        e_popped_dates.remove(filing.last_end_date)


def test_pop_duplicates_3languages_2enclosures_filing_index_none(
        ageas21_22_filingset):
    """Test pop_duplicates method with 3 languages, 2 enclosures, max filing_index as None."""
    fs: xf.FilingSet = ageas21_22_filingset
    for filing in fs:
        if filing.filing_index in (
                '5493005DJBML6LY3RV36-2021-12-31-ESEF-BE-2',
                '5493005DJBML6LY3RV36-2022-12-31-ESEF-BE-2'):
            filing.filing_index = None
    popped = fs.pop_duplicates(
        languages=None,
        use_reporting_date=False,
        all_markets=False
        )
    assert isinstance(fs, xf.FilingSet)
    assert len(fs) == 2
    e_retained_dates = [date(2021, 12, 31), date(2022, 12, 31)]
    e_max_filing_indexes = (
        '5493005DJBML6LY3RV36-2021-12-31-ESEF-BE-1',
        '5493005DJBML6LY3RV36-2022-12-31-ESEF-BE-1'
        )
    for filing in fs:
        assert filing.filing_index in e_max_filing_indexes
        e_retained_dates.remove(filing.last_end_date)

    assert isinstance(popped, xf.FilingSet)
    assert len(popped) == 4
    e_popped_dates = [
        date(2021, 12, 31), date(2021, 12, 31), date(2022, 12, 31),
        date(2022, 12, 31)
        ]
    for filing in popped:
        assert filing.filing_index not in e_max_filing_indexes
        e_popped_dates.remove(filing.last_end_date)


def test_pop_duplicates_use_reporting_date_false_faulty_last_end_date(
        applus20_21_filingset):
    """Test pop_duplicates method with faulty last_end_date, use_reporting_date=False."""
    fs: xf.FilingSet = applus20_21_filingset
    popped = fs.pop_duplicates(
        languages=None,
        use_reporting_date=False,
        all_markets=False
        )
    assert isinstance(fs, xf.FilingSet)
    assert len(fs) == 1
    e_max_filing_index = (
        '213800M9XCA6NR98E873-2021-12-31-ESEF-ES-1')
    filing = next(iter(fs))
    assert filing.filing_index == e_max_filing_index
    assert filing.last_end_date == date(2021, 12, 31)

    assert isinstance(popped, xf.FilingSet)
    assert len(popped) == 1
    filing = next(iter(popped))
    assert filing.filing_index != e_max_filing_index
    assert filing.last_end_date == date(2021, 12, 31)


def test_pop_duplicates_use_reporting_date_true_faulty_last_end_date(
        applus20_21_filingset):
    """Test pop_duplicates method with faulty last_end_date, use_reporting_date=True."""
    fs: xf.FilingSet = applus20_21_filingset
    popped = fs.pop_duplicates(
        languages=None,
        use_reporting_date=True,
        all_markets=False
        )
    assert isinstance(fs, xf.FilingSet)
    assert len(fs) == 2
    for filing in fs:
        assert filing.last_end_date in [date(2020, 12, 31), date(2021, 12, 31)]

    assert isinstance(popped, xf.FilingSet)
    assert len(popped) == 0
