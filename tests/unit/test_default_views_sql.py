"""Define tests for `default_views.DEFAULT_VIEWS` SQL views."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import sqlite3
import subprocess

import pytest

import xbrl_filings_api as xf
from xbrl_filings_api.default_views import DEFAULT_VIEWS


def _db_with_view(db_path, view, schema):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    for table_name, cols in schema.items():
        colsql = ', '.join(cols)
        cur.executescript(f'CREATE TABLE {table_name} ({colsql}) WITHOUT ROWID')
    con.commit()
    cur.executescript(f'CREATE VIEW {view.name} AS\n{view.sql}')
    con.commit()
    return con, cur


def _insert_many(con, cur, table_name, rowdicts):
    col_names = tuple(rowdicts[0].keys())
    values = []
    for rowdict in rowdicts:
        values.append(tuple(rowdict[col] for col in col_names))
    placeholder_sql = ', '.join(['?'] * len(col_names))
    col_sql = ', '.join(col_names)
    cur.executemany(
        f'INSERT INTO {table_name} ({col_sql}) '
        f'VALUES ({placeholder_sql})',
        values
        )
    con.commit()


def _insert_example_group_fi(con, cur):
    """Filing api_id=1, Entity api_id=10."""
    _insert_many(con, cur, 'Filing', [{
        'api_id': '1',
        'reporting_date': '2022-12-31',
        'language': 'fi',
        'entity_api_id': '10'
    }])
    _insert_many(con, cur, 'Entity', [{
        'api_id': '10',
        'name': 'Example Group Oyj'
    }])


def _view_row_count(cur, view_name):
    cur.execute(f'SELECT count(*) FROM {view_name}')
    return cur.fetchone()[0]


def _insert_example_calc_vmessage(con, cur, api_id, filing_api_id):
    _insert_many(con, cur, 'ValidationMessage', [{
            'api_id': api_id,
            'duplicate_lesser': None,
            'duplicate_greater': None,
            'code': 'xbrl.5.2.5.2:calcInconsistency',
            'calc_reported_sum': 35_641_000.0,
            'calc_computed_sum': 29_640_000.0,
            'calc_line_item': 'ifrs-full:EquityAttributableToOwnersOfParent',
            'calc_short_role': 'StmtOfFinancialPosition',
            'calc_context_id': 'E2021',
            'filing_api_id': filing_api_id
        }])


def _insert_example_duplicate_vmessage(con, cur, api_id, filing_api_id):
    _insert_many(con, cur, 'ValidationMessage', [{
            'api_id': api_id,
            'duplicate_lesser': 31_821_000.0,
            'duplicate_greater': 38_417_000.0,
            'code': 'message:tech_duplicated_facts1',
            'calc_reported_sum': None,
            'calc_computed_sum': None,
            'calc_line_item': None,
            'calc_short_role': None,
            'calc_context_id': None,
            'filing_api_id': filing_api_id
        }])


@pytest.fixture
def db_ViewNumericErrors(tmp_path):
    db_path = tmp_path / 'db_ViewNumericErrors.db'
    view = next(
        v for v in DEFAULT_VIEWS if v.name == 'ViewNumericErrors')
    schema = {
        'Filing': [
            'api_id TEXT PRIMARY KEY', 'reporting_date TEXT', 'language TEXT',
            'entity_api_id TEXT'
            ],
        'Entity': ['api_id TEXT PRIMARY KEY', 'name TEXT'],
        'ValidationMessage': [
            'api_id TEXT PRIMARY KEY', 'duplicate_lesser REAL',
            'duplicate_greater REAL', 'code TEXT', 'calc_reported_sum REAL',
            'calc_computed_sum REAL', 'calc_line_item TEXT',
            'calc_short_role TEXT', 'calc_context_id TEXT',
            'filing_api_id TEXT'
            ]
        }
    con, cur = _db_with_view(db_path, view, schema)
    return db_path, con, cur


@pytest.mark.sqlite
def test_ViewNumericErrors_calc(db_ViewNumericErrors):
    """Test typical ViewNumericErrors problem=calc."""
    e_reported = 35_641_000.0
    e_computed = 29_640_000.0
    cur: sqlite3.Cursor
    db_path, con, cur = db_ViewNumericErrors
    _insert_example_group_fi(con, cur)
    _insert_many(con, cur, 'ValidationMessage', [{
            'api_id': '100',
            'duplicate_lesser': None,
            'duplicate_greater': None,
            'code': 'xbrl.5.2.5.2:calcInconsistency',
            'calc_reported_sum': e_reported,
            'calc_computed_sum': e_computed,
            'calc_line_item': 'ifrs-full:EquityAttributableToOwnersOfParent',
            'calc_short_role': 'StmtOfFinancialPosition',
            'calc_context_id': 'E2021',
            'filing_api_id': '1'
        }])

    assert _view_row_count(cur, 'ViewNumericErrors') == 1
    cur.execute(
        'SELECT entity_name, reporting_date, problem, reportedK, '
        'computedOrDuplicateK, reportedErrorK, errorPercent, calc_line_item, '
        'calc_short_role, calc_context_id, language, filing_api_id, '
        'entity_api_id, validation_message_api_id '
        'FROM ViewNumericErrors'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'Example Group Oyj' # entity_name
    assert res[1] == '2022-12-31' # reporting_date
    assert res[2] == 'calc' # problem
    assert res[3] == e_reported / 1000 # reportedK
    assert res[4] == e_computed / 1000 # computedOrDuplicateK
    assert res[5] == abs(e_reported - e_computed) / 1000 # reportedErrorK
    assert res[6] == round(100 * (abs(e_reported-e_computed) / e_reported), 2) # errorPercent
    assert res[7] == 'ifrs-full:EquityAttributableToOwnersOfParent' # calc_line_item
    assert res[8] == 'StmtOfFinancialPosition' # calc_short_role
    assert res[9] == 'E2021' # calc_context_id
    assert res[10] == 'fi' # language
    assert res[11] == '1' # filing_api_id
    assert res[12] == '10' # entity_api_id
    # subprocess.run((
    #     r'C:\Users\malff\AppData\Local\Programs\DB Browser for SQLite\DB Browser for SQLite.exe',
    #     str(db_path)
    #     ))


@pytest.mark.sqlite
def test_ViewNumericErrors_duplicate(db_ViewNumericErrors):
    """Test typical ViewNumericErrors problem=duplicate."""
    e_lesser = 31_821_000.0
    e_greater = 38_417_000.0
    cur: sqlite3.Cursor
    db_path, con, cur = db_ViewNumericErrors
    _insert_example_group_fi(con, cur)
    _insert_many(con, cur, 'ValidationMessage', [{
            'api_id': '100',
            'duplicate_lesser': e_lesser,
            'duplicate_greater': e_greater,
            'code': 'message:tech_duplicated_facts1',
            'calc_reported_sum': None,
            'calc_computed_sum': None,
            'calc_line_item': None,
            'calc_short_role': None,
            'calc_context_id': None,
            'filing_api_id': '1'
        }])

    assert _view_row_count(cur, 'ViewNumericErrors') == 1
    cur.execute(
        'SELECT entity_name, reporting_date, problem, reportedK, '
        'computedOrDuplicateK, reportedErrorK, errorPercent, calc_line_item, '
        'calc_short_role, calc_context_id, language, filing_api_id, '
        'entity_api_id, validation_message_api_id '
        'FROM ViewNumericErrors'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'Example Group Oyj' # entity_name
    assert res[1] == '2022-12-31' # reporting_date
    assert res[2] == 'duplicate' # problem
    assert res[3] == e_lesser / 1000 # reportedK
    assert res[4] == e_greater / 1000 # computedOrDuplicateK
    assert res[5] == abs(e_lesser-e_greater) / 1000 # reportedErrorK
    assert res[6] == round(100 * (abs(e_lesser-e_greater) / e_lesser), 2) # errorPercent
    assert res[7] == None # calc_line_item
    assert res[8] == None # calc_short_role
    assert res[9] == None # calc_context_id
    assert res[10] == 'fi' # language
    assert res[11] == '1' # filing_api_id
    assert res[12] == '10' # entity_api_id


@pytest.mark.sqlite
def test_ViewNumericErrors_select_language_fi_not_gi(db_ViewNumericErrors):
    """Test ViewNumericErrors selects language version 'fi', not 'gi'."""
    cur: sqlite3.Cursor
    db_path, con, cur = db_ViewNumericErrors
    _insert_example_group_fi(con, cur)
    _insert_many(con, cur, 'Filing', [{
        'api_id': '2',
        'reporting_date': '2022-12-31',
        'language': 'gi',
        'entity_api_id': '10'
    }])
    _insert_example_calc_vmessage(con, cur, api_id='102', filing_api_id='1')
    _insert_example_calc_vmessage(con, cur, api_id='103', filing_api_id='2')

    assert _view_row_count(cur, 'ViewNumericErrors') == 1
    cur.execute(
        'SELECT language, filing_api_id, validation_message_api_id '
        'FROM ViewNumericErrors'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'fi' # language
    assert res[1] == '1' # filing_api_id
    assert res[2] == '102' # validation_message_api_id


@pytest.mark.sqlite
def test_ViewNumericErrors_select_language_ei_not_fi(db_ViewNumericErrors):
    """Test ViewNumericErrors selects language version 'ei', not 'fi'."""
    cur: sqlite3.Cursor
    db_path, con, cur = db_ViewNumericErrors
    _insert_example_group_fi(con, cur)
    _insert_many(con, cur, 'Filing', [{
        'api_id': '2',
        'reporting_date': '2022-12-31',
        'language': 'ei',
        'entity_api_id': '10'
    }])
    _insert_example_calc_vmessage(con, cur, api_id='102', filing_api_id='1')
    _insert_example_calc_vmessage(con, cur, api_id='103', filing_api_id='2')

    assert _view_row_count(cur, 'ViewNumericErrors') == 1
    cur.execute(
        'SELECT language, filing_api_id, validation_message_api_id '
        'FROM ViewNumericErrors'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'ei' # language
    assert res[1] == '2' # filing_api_id
    assert res[2] == '103' # validation_message_api_id


@pytest.mark.sqlite
def test_ViewNumericErrors_select_language_null_not_fi(db_ViewNumericErrors):
    """Test ViewNumericErrors selects language version NULL, not 'fi'."""
    cur: sqlite3.Cursor
    db_path, con, cur = db_ViewNumericErrors
    _insert_example_group_fi(con, cur)
    _insert_many(con, cur, 'Filing', [{
        'api_id': '2',
        'reporting_date': '2022-12-31',
        'language': None,
        'entity_api_id': '10'
    }])
    _insert_example_calc_vmessage(con, cur, api_id='102', filing_api_id='1')
    _insert_example_calc_vmessage(con, cur, api_id='103', filing_api_id='2')

    assert _view_row_count(cur, 'ViewNumericErrors') == 1
    cur.execute(
        'SELECT language, filing_api_id, validation_message_api_id '
        'FROM ViewNumericErrors'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == None # language
    assert res[1] == '2' # filing_api_id
    assert res[2] == '103' # validation_message_api_id


@pytest.mark.sqlite
def test_ViewNumericErrors_duplicate_reduce_multiples(db_ViewNumericErrors):
    """Test ViewNumericErrors problem=duplicate when same duplicate recorded multiple times."""
    cur: sqlite3.Cursor
    db_path, con, cur = db_ViewNumericErrors
    _insert_example_group_fi(con, cur)
    # All have same ``duplicate_lesser`` and ``duplicate_greater``
    _insert_example_duplicate_vmessage(con, cur, api_id='100', filing_api_id='1')
    _insert_example_duplicate_vmessage(con, cur, api_id='101', filing_api_id='1')
    _insert_example_duplicate_vmessage(con, cur, api_id='102', filing_api_id='1')

    assert _view_row_count(cur, 'ViewNumericErrors') == 1
    cur.execute(
        'SELECT problem, filing_api_id, entity_api_id, validation_message_api_id '
        'FROM ViewNumericErrors'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'duplicate' # problem
    assert res[1] == '1' # filing_api_id
    assert res[2] == '10' # entity_api_id
    assert res[3] in ('100', '101', '102') # validation_message_api_id


@pytest.mark.sqlite
def test_ViewNumericErrors_calc_dont_reduce_multiples(db_ViewNumericErrors):
    """Test ViewNumericErrors problem=calc when similar errors recorded multiple times."""
    cur: sqlite3.Cursor
    db_path, con, cur = db_ViewNumericErrors
    _insert_example_group_fi(con, cur)
    # All have same ``calc_reported_sum`` and ``calc_computed_sum``
    _insert_example_calc_vmessage(con, cur, api_id='100', filing_api_id='1')
    _insert_example_calc_vmessage(con, cur, api_id='101', filing_api_id='1')
    _insert_example_calc_vmessage(con, cur, api_id='102', filing_api_id='1')

    assert _view_row_count(cur, 'ViewNumericErrors') == 3
    cur.execute(
        'SELECT problem, filing_api_id, entity_api_id, validation_message_api_id '
        'FROM ViewNumericErrors'
        )
    for _ in range(3):
        res = cur.fetchone()
        assert res[0] == 'calc' # problem
        assert res[1] == '1' # filing_api_id
        assert res[2] == '10' # entity_api_id
        assert res[3] in ('100', '101', '102') # validation_message_api_id
    con.close()


# next(v for v in xf.default_views.DEFAULT_VIEWS if v.name == 'ViewEnclosure')
# next(v for v in xf.default_views.DEFAULT_VIEWS if v.name == 'ViewFilingAge')