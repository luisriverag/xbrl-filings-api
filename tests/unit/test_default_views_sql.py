"""Define tests for `default_views.DEFAULT_VIEWS` SQL views."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import sqlite3

import pytest

import xbrl_filings_api as xf
from xbrl_filings_api.default_views import DEFAULT_VIEWS

pytestmark = pytest.mark.sqlite


def _db_with_view(view, schema):
    con = sqlite3.connect(':memory:')
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


def _view_row_count(cur, view_name):
    cur.execute(f'SELECT count(*) FROM {view_name}')
    return cur.fetchone()[0]


def _insert_example_group_fi_ViewNumericErrors(con, cur):
    """Filing api_id=1, Entity api_id=10."""
    _insert_many(con, cur, 'Entity', [{
        'api_id': '10',
        'name': 'Example Group Oyj'
        }])
    _insert_many(con, cur, 'Filing', [{
        'api_id': '1',
        'reporting_date': '2022-12-31',
        'language': 'fi',
        'entity_api_id': '10'
        }])


def _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id, filing_api_id):
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


def _insert_example_duplicate_vmessage_ViewNumericErrors(con, cur, api_id, filing_api_id):
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
    view = next(v for v in DEFAULT_VIEWS if v.name == 'ViewNumericErrors')
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
    con, cur = _db_with_view(view, schema)
    return con, cur


@pytest.fixture
def db_ViewEnclosure(tmp_path):
    view = next(v for v in DEFAULT_VIEWS if v.name == 'ViewEnclosure')
    schema = {
        'Filing': [
            'api_id TEXT PRIMARY KEY', 'reporting_date TEXT', 'country TEXT',
            'language TEXT', 'error_count INTEGER',
            'inconsistency_count INTEGER', 'warning_count INTEGER',
            'added_time TEXT', 'processed_time TEXT',
            'entity_api_id TEXT'
            ],
        'Entity': ['api_id TEXT PRIMARY KEY', 'name TEXT', 'identifier TEXT']
        }
    con, cur = _db_with_view(view, schema)
    return con, cur


@pytest.fixture
def db_ViewFilingAge(tmp_path):
    view = next(v for v in DEFAULT_VIEWS if v.name == 'ViewFilingAge')
    schema = {
        'Filing': [
            'api_id TEXT PRIMARY KEY', 'reporting_date TEXT', 'country TEXT',
            'language TEXT', 'added_time TEXT', 'processed_time TEXT',
            'entity_api_id TEXT'
            ],
        'Entity': ['api_id TEXT PRIMARY KEY', 'name TEXT', 'identifier TEXT']
        }
    con, cur = _db_with_view(view, schema)
    return con, cur


def test_ViewNumericErrors_calc(db_ViewNumericErrors):
    """Test typical ViewNumericErrors problem=calc."""
    e_reported = 35_641_000.0
    e_computed = 29_640_000.0
    cur: sqlite3.Cursor
    con, cur = db_ViewNumericErrors
    _insert_example_group_fi_ViewNumericErrors(con, cur)
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


def test_ViewNumericErrors_duplicate(db_ViewNumericErrors):
    """Test typical ViewNumericErrors problem=duplicate."""
    e_lesser = 31_821_000.0
    e_greater = 38_417_000.0
    cur: sqlite3.Cursor
    con, cur = db_ViewNumericErrors
    _insert_example_group_fi_ViewNumericErrors(con, cur)
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


def test_ViewNumericErrors_select_language_fi_not_gi(db_ViewNumericErrors):
    """Test ViewNumericErrors selects language version 'fi', not 'gi'."""
    cur: sqlite3.Cursor
    con, cur = db_ViewNumericErrors
    _insert_example_group_fi_ViewNumericErrors(con, cur)
    _insert_many(con, cur, 'Filing', [{
        'api_id': '2',
        'reporting_date': '2022-12-31',
        'language': 'gi',
        'entity_api_id': '10'
        }])
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='102', filing_api_id='1')
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='103', filing_api_id='2')

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


def test_ViewNumericErrors_select_language_ei_not_fi(db_ViewNumericErrors):
    """Test ViewNumericErrors selects language version 'ei', not 'fi'."""
    cur: sqlite3.Cursor
    con, cur = db_ViewNumericErrors
    _insert_example_group_fi_ViewNumericErrors(con, cur)
    _insert_many(con, cur, 'Filing', [{
        'api_id': '2',
        'reporting_date': '2022-12-31',
        'language': 'ei',
        'entity_api_id': '10'
        }])
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='102', filing_api_id='1')
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='103', filing_api_id='2')

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


def test_ViewNumericErrors_select_language_null_not_fi(db_ViewNumericErrors):
    """Test ViewNumericErrors selects language version NULL, not 'fi'."""
    cur: sqlite3.Cursor
    con, cur = db_ViewNumericErrors
    _insert_example_group_fi_ViewNumericErrors(con, cur)
    _insert_many(con, cur, 'Filing', [{
        'api_id': '2',
        'reporting_date': '2022-12-31',
        'language': None,
        'entity_api_id': '10'
        }])
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='102', filing_api_id='1')
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='103', filing_api_id='2')

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


def test_ViewNumericErrors_duplicate_reduce_multiples(db_ViewNumericErrors):
    """Test ViewNumericErrors problem=duplicate when same duplicate recorded multiple times."""
    cur: sqlite3.Cursor
    con, cur = db_ViewNumericErrors
    _insert_example_group_fi_ViewNumericErrors(con, cur)
    # All have same ``duplicate_lesser`` and ``duplicate_greater``
    _insert_example_duplicate_vmessage_ViewNumericErrors(con, cur, api_id='100', filing_api_id='1')
    _insert_example_duplicate_vmessage_ViewNumericErrors(con, cur, api_id='101', filing_api_id='1')
    _insert_example_duplicate_vmessage_ViewNumericErrors(con, cur, api_id='102', filing_api_id='1')

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


def test_ViewNumericErrors_calc_dont_reduce_multiples(db_ViewNumericErrors):
    """Test ViewNumericErrors problem=calc when similar errors recorded multiple times."""
    cur: sqlite3.Cursor
    con, cur = db_ViewNumericErrors
    _insert_example_group_fi_ViewNumericErrors(con, cur)
    # All have same ``calc_reported_sum`` and ``calc_computed_sum``
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='100', filing_api_id='1')
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='101', filing_api_id='1')
    _insert_example_calc_vmessage_ViewNumericErrors(con, cur, api_id='102', filing_api_id='1')

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


def test_ViewEnclosure_one_filing(db_ViewEnclosure):
    """Test ViewEnclosure with a single language filing."""
    cur: sqlite3.Cursor
    con, cur = db_ViewEnclosure
    _insert_many(con, cur, 'Entity', [{
        'api_id': '10',
        'name': 'Example Group Oyj',
        'identifier': '724500Y6DUVHQD6OXN27'
        }])
    _insert_many(con, cur, 'Filing', [{
        'api_id': '1',
        'reporting_date': '2022-12-31',
        'country': 'FI',
        'language': 'fi',
        'error_count': 1,
        'inconsistency_count': 2,
        'warning_count': 3,
        'added_time': '2024-02-29 12:17:45.429217',
        'processed_time': '2024-03-01 13:03:23.593280',
        'entity_api_id': '10'
        }])

    assert _view_row_count(cur, 'ViewEnclosure') == 1
    cur.execute(
        'SELECT entity_name, reporting_date, country, filing_count, '
        'languages, filingApiIds, error_count, inconsistency_count, '
        'warning_count, added_time, processed_time, entity_identifier, '
        'entity_api_id '
        'FROM ViewEnclosure'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'Example Group Oyj' # entity_name
    assert res[1] == '2022-12-31' # reporting_date
    assert res[2] == 'FI' # country
    assert res[3] == 1 # filing_count
    assert res[4] == 'fi' # languages
    assert res[5] == '1' # filingApiIds
    assert res[6] == 1 # error_count
    assert res[7] == 2 # inconsistency_count
    assert res[8] == 3 # warning_count
    assert res[9] == '2024-02-29 12:17:45.429217' # added_time
    assert res[10] == '2024-03-01 13:03:23.593280' # processed_time
    assert res[11] == '724500Y6DUVHQD6OXN27' # entity_identifier
    assert res[12] == '10' # entity_api_id


def test_ViewEnclosure_3_filings(db_ViewEnclosure):
    """Test ViewEnclosure with three language filings."""
    cur: sqlite3.Cursor
    con, cur = db_ViewEnclosure
    _insert_many(con, cur, 'Entity', [{
        'api_id': '10',
        'name': 'Example Group Oyj',
        'identifier': '724500Y6DUVHQD6OXN27'
        }])
    _insert_many(con, cur, 'Filing', [
        {
            'api_id': '1',
            'reporting_date': '2022-12-31',
            'country': 'FI',
            'language': 'fi',
            'error_count': 1,
            'inconsistency_count': 10,
            'warning_count': 4,
            'added_time': '2024-01-02 12:17:45.429521',
            'processed_time': '2024-03-02 13:03:23.593280',
            'entity_api_id': '10'
        },
        {
            'api_id': '2',
            'reporting_date': '2022-12-31',
            'country': 'FI',
            'language': None,
            'error_count': 5,
            'inconsistency_count': 0,
            'warning_count': 3,
            'added_time': '2024-02-01 12:17:45.429217',
            'processed_time': '2024-03-01 13:03:23.593280',
            'entity_api_id': '10'
        },
        {
            'api_id': '3',
            'reporting_date': '2022-12-31',
            'country': 'FI',
            'language': 'en',
            'error_count': 2,
            'inconsistency_count': 1,
            'warning_count': 15,
            'added_time': '2024-01-31 12:17:45.429217',
            'processed_time': '2024-03-14 13:03:23.593521',
            'entity_api_id': '10'
        },
        ])

    assert _view_row_count(cur, 'ViewEnclosure') == 1
    cur.execute(
        'SELECT entity_name, reporting_date, country, filing_count, '
        'languages, filingApiIds, error_count, inconsistency_count, '
        'warning_count, added_time, processed_time, entity_identifier, '
        'entity_api_id '
        'FROM ViewEnclosure'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'Example Group Oyj' # entity_name
    assert res[1] == '2022-12-31' # reporting_date
    assert res[2] == 'FI' # country
    assert res[3] == 3 # filing_count
    assert res[4] == 'en, fi' # languages
    assert res[5] == '3, 1, 2' # filingApiIds
    assert res[6] == 5 # error_count
    assert res[7] == 10 # inconsistency_count
    assert res[8] == 15 # warning_count
    assert res[9] == '2024-01-02 12:17:45.429521' # added_time
    assert res[10] == '2024-03-14 13:03:23.593521' # processed_time
    assert res[11] == '724500Y6DUVHQD6OXN27' # entity_identifier
    assert res[12] == '10' # entity_api_id


def test_ViewFilingAge(db_ViewFilingAge):
    """Test typical ViewFilingAge case."""
    cur: sqlite3.Cursor
    con, cur = db_ViewFilingAge
    _insert_many(con, cur, 'Entity', [{
        'api_id': '10',
        'name': 'Example Group Oyj',
        'identifier': '724500Y6DUVHQD6OXN27'
        }])
    _insert_many(con, cur, 'Filing', [{
        'api_id': '1',
        'reporting_date': '2022-12-31',
        'country': 'FI',
        'language': 'fi',
        'added_time': '2024-01-01 12:00:00.000000',
        'processed_time': '2024-01-02 12:00:00.000000',
        'entity_api_id': '10'
        }])

    assert _view_row_count(cur, 'ViewFilingAge') == 1
    cur.execute(
        'SELECT entity_name, reporting_date, language, dataAgeDays, country, '
        'added_time, processed_time, addedToProcessedDays, filing_api_id, '
        'entity_api_id '
        'FROM ViewFilingAge'
        )
    res = cur.fetchone()
    con.close()
    assert res[0] == 'Example Group Oyj' # entity_name
    assert res[1] == '2022-12-31' # reporting_date
    assert res[2] == 'fi' # language
    # dataAgeDays is untestable
    assert res[4] == 'FI' # country
    assert res[5] == '2024-01-01 12:00:00.000000' # added_time
    assert res[6] == '2024-01-02 12:00:00.000000' # processed_time
    assert res[7] == 1 # addedToProcessedDays
    assert res[8] == '1' # filing_api_id
    assert res[9] == '10' # entity_api_id


def test_ViewFilingAge_addedToProcessedDays_nearly_one(db_ViewFilingAge):
    """Test ViewFilingAge addedToProcessedDays=0 due to not quite 1."""
    cur: sqlite3.Cursor
    con, cur = db_ViewFilingAge
    _insert_many(con, cur, 'Entity', [{
        'api_id': '10',
        'name': 'Example Group Oyj',
        'identifier': '724500Y6DUVHQD6OXN27'
        }])
    _insert_many(con, cur, 'Filing', [{
        'api_id': '1',
        'reporting_date': '2022-12-31',
        'country': 'FI',
        'language': 'fi',
        'added_time': '2024-01-01 12:00:00.001000',
        'processed_time': '2024-01-02 12:00:00.000000',
        'entity_api_id': '10'
        }])

    assert _view_row_count(cur, 'ViewFilingAge') == 1
    cur.execute(
        'SELECT added_time, processed_time, addedToProcessedDays '
        'FROM ViewFilingAge'
        )
    res = cur.fetchone()
    con.close()
    # Time resolution of SQLite is milliseconds
    assert res[0] == '2024-01-01 12:00:00.001000' # added_time
    assert res[1] == '2024-01-02 12:00:00.000000' # processed_time
    assert res[2] == 0 # addedToProcessedDays


def test_ViewFilingAge_addedToProcessedDays_one_and_half(db_ViewFilingAge):
    """Test ViewFilingAge addedToProcessedDays=1 when its 1.5."""
    cur: sqlite3.Cursor
    con, cur = db_ViewFilingAge
    _insert_many(con, cur, 'Entity', [{
        'api_id': '10',
        'name': 'Example Group Oyj',
        'identifier': '724500Y6DUVHQD6OXN27'
        }])
    _insert_many(con, cur, 'Filing', [{
        'api_id': '1',
        'reporting_date': '2022-12-31',
        'country': 'FI',
        'language': 'fi',
        'added_time': '2024-01-01 12:00:00.000000',
        'processed_time': '2024-01-03 00:00:00.000000',
        'entity_api_id': '10'
        }])

    assert _view_row_count(cur, 'ViewFilingAge') == 1
    cur.execute(
        'SELECT added_time, processed_time, addedToProcessedDays '
        'FROM ViewFilingAge'
        )
    res = cur.fetchone()
    con.close()
    # Time resolution of SQLite is milliseconds
    assert res[0] == '2024-01-01 12:00:00.000000' # added_time
    assert res[1] == '2024-01-03 00:00:00.000000' # processed_time
    assert res[2] == 1 # addedToProcessedDays
