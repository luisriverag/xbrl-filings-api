"""
Module for processing SQLite3 databases.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from pathlib import Path
from collections.abc import Generator, Iterable
import sqlite3

from .api_object.api_resource import APIResource
from .api_object.entity import Entity
from .api_object.filing import Filing
from .api_object.filings_page import FilingsPage
from .api_object.validation_message import ValidationMessage
from .enums import (
    ScopeFlag, GET_ONLY_FILINGS, GET_ENTITY, GET_VALIDATION_MESSAGES)
from .exceptions import (
    DatabaseFileExistsError, DatabasePathIsReservedError,
    DatabaseSchemaUnmatch
    )
from .time_formats import time_formats
import xbrl_filings_api.order_columns as order_columns
import xbrl_filings_api.options as options

CurrentSchemaType = dict[str, list[str]]
"""`{'TableName': ['col1', 'col2', ...]}`"""


def sets_to_sqlite(
        flags: ScopeFlag,
        ppath: Path,
        update: bool,
        data_objs: dict[str, Iterable[APIResource]],
        ) -> None:
    """
    Save sets to SQLite3 database.

    Raises
    ------
    DatabaseFileExistsError
    DatabasePathIsReservedError
    DatabaseSchemaUnmatch
    sqlite3.DatabaseError
    """
    _validate_path(update, ppath)
    filing_data_attrs = Filing.get_data_attributes(
        flags, data_objs['Filing'])
    con, table_schema = _create_database_or_extend_schema(
        flags, ppath, update, filing_data_attrs)
    _insert_data(table_schema, data_objs, con)
    con.close()


def pages_to_sqlite(
        flags: ScopeFlag,
        ppath: Path,
        update: bool,
        page_gen: Generator[FilingsPage, None, None],
        ) -> None:
    """
    Save API pages to SQLite3 database.

    Raises
    ------
    DatabaseFileExistsError
    DatabasePathIsReservedError
    DatabaseSchemaUnmatch
    sqlite3.DatabaseError
    """
    _validate_path(update, ppath)
    filing_data_attrs = Filing.get_data_attributes(flags)
    con, table_schema = _create_database_or_extend_schema(
        flags, ppath, update, filing_data_attrs)

    for page in page_gen:
        entities: list[Entity] = []
        messages: list[ValidationMessage] = []
        for filing in page.filing_list:
            if filing.entity:
                entities.append(filing.entity)
            if filing.validation_messages:
                messages.extend(filing.validation_messages)
        data_objs: dict[str, Iterable[APIResource]] = {
            'Filing': page.filing_list,
            'Entity': entities,
            'ValidationMessage': messages
            }
        _insert_data(table_schema, data_objs, con)
    con.close()


def _validate_path(update: bool, ppath: Path) -> None:
    """
    When file exists in path, raise if ``update=False`` and raise if
    path is reserved.

    Raises
    ------
    DatabaseFileExistsError
    DatabasePathIsReservedError
    """
    if ppath.is_file():
        if not update:
            raise DatabaseFileExistsError(str(ppath))
    elif ppath.exists():
        raise DatabasePathIsReservedError(str(ppath))


def _create_database_or_extend_schema(
        flags: ScopeFlag, db_path: Path, update: bool,
        filing_data_attrs: list[str]
        ) -> tuple[sqlite3.Connection, CurrentSchemaType]:
    """
    Creates an SQLite3 database or extends the tables and columns of
    an existing database.
    
    Returns
    -------
    tuple of sqlite3.Connection, CurrentSchemaType
        ``(con, table_schema)``.

    Raises
    ------
    DatabaseSchemaUnmatch
    sqlite3.DatabaseError
    """
    resource_types: list[type[APIResource]] = [Filing]
    data_attrs = {'Filing': filing_data_attrs}
    if GET_ONLY_FILINGS not in flags:
        if GET_ENTITY in flags:
            resource_types.append(Entity)
            data_attrs['Entity'] = Entity.get_data_attributes()
        if GET_VALIDATION_MESSAGES in flags:
            resource_types.append(ValidationMessage)
            data_attrs['ValidationMessage'] = (
                ValidationMessage.get_data_attributes())
    
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    cur = connection.cursor()
    table_names = {cls.__name__ for cls in resource_types}
    existing_tables: set[str] = set()
    existing_views: set[str] = set()

    if update:
        schema_match = False
        _exec(
            cur,
            "SELECT type, name FROM sqlite_schema "
            "WHERE name NOT LIKE 'sqlite_%'"
            )
        db_objs = cur.fetchall()
        existing_tables = {row[1] for row in db_objs if row[0] == 'table'}
        existing_views = {row[1] for row in db_objs if row[0] == 'view'}
        for table_name in existing_tables:
            if table_name in table_names:
                schema_match = True
                break
        if not schema_match:
            path = str(db_path)
            raise DatabaseSchemaUnmatch(path)

    table_schema: CurrentSchemaType = dict()
    for type_obj in resource_types:
        table_name = type_obj.__name__
        cols = data_attrs[table_name]
        
        col_defs = _get_col_defs(cols)
        table_schema[table_name] = [cd[0] for cd in col_defs]

        if table_name in existing_tables:
            schema_match = False
            _exec(
                cur,
                f"SELECT name FROM pragma_table_info('{table_name}')"
                )
            existing_cols = [row[0] for row in cur.fetchall()]
            add_cols = []
            for col in cols:
                try:
                    existing_cols.index(col)
                except ValueError:
                    add_cols.append(col)
                else:
                    schema_match = True
            if not schema_match or 'api_id' not in cols:
                path = str(db_path)
                raise DatabaseSchemaUnmatch(path)
            for col, tc in _get_col_defs(add_cols):
                _exec(
                    cur,
                    f"ALTER TABLE {table_name} ADD COLUMN {col} {tc}"
                    )
                table_schema[table_name].append(col)
            connection.commit()
            continue

        _exec(
            cur,
            f"CREATE TABLE {table_name} (\n  "
            + ",\n  ".join((' '.join(cd) for cd in col_defs))
            + "\n) WITHOUT ROWID"
            )
        connection.commit()
    
    if options.views:
        for view_name, (required_tables, view_sql) in options.views.items():
            if view_name in existing_views:
                continue
            for table_name in required_tables:
                if table_name not in table_schema:
                    continue
            _exec(
                cur,
                f"CREATE VIEW {view_name}\n"
                "AS" + view_sql.rstrip()
                )
            connection.commit()
    return connection, table_schema


def _get_col_defs(cols: list[str]) -> list[tuple[str, str]]:
    """Get list of (col_name, type_const)."""
    cols = order_columns.order_columns(cols)
    col_defs = []
    for col in cols:
        type_const = 'TEXT'
        if col.endswith('_count'):
            type_const = 'INTEGER'
        elif col.endswith('_sum') or col.startswith('duplicate_'):
            type_const = 'REAL'
        if col == 'api_id':
            type_const += ' PRIMARY KEY NOT NULL'
        col_defs.append((col, type_const))
    return col_defs


def _insert_data(
        table_schema: CurrentSchemaType,
        data_objs: dict[str, Iterable[APIResource]],
        con: sqlite3.Connection):
    cur = con.cursor()
    for table_name in table_schema:
        cols = table_schema[table_name]
        records = [
            [getattr(item, col) for col in cols]
            for item in data_objs[table_name]
            ]
        colsql = '\n  ' + ',\n  '.join(cols) + '\n  '
        phs = ', '.join(['?'] * len(cols))
        _exec(
            cur,
            f"REPLACE INTO {table_name} ({colsql})\nVALUES ({phs})",
            records
            )
        con.commit()


def _exec(cur: sqlite3.Cursor, sql: str, data: list[list[str]] | None = None) -> None:
    data_len = f' <count: {len(data)}>' if data else ''
    print(sql + ';' + data_len)

    if data:
        cur.executemany(sql, data)
    else:
        cur.execute(sql)


def adapt_datetime(dt: datetime):
    try:
        fstr = time_formats[options.time_accuracy]
    except KeyError:
        fstr = time_formats['min']
    return dt.strftime(fstr)


def adapt_list(list_in: list):
    return '\n'.join(list_in)


sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_adapter(list, adapt_list)
