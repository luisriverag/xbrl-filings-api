"""Module for processing SQLite3 databases."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Double quotes are used in all SQL strings by default.
# ruff: noqa: Q000

import logging
import sqlite3
from collections.abc import Generator, Iterable
from datetime import datetime
from pathlib import Path

import xbrl_filings_api.options as options
import xbrl_filings_api.order_columns as order_columns
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    ScopeFlag,
)
from xbrl_filings_api.exceptions import (
    DatabaseFileExistsError,
    DatabasePathIsReservedError,
    DatabaseSchemaUnmatchError,
)
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.filings_page import FilingsPage
from xbrl_filings_api.time_formats import time_formats
from xbrl_filings_api.validation_message import ValidationMessage

logger = logging.getLogger(__name__)

CurrentSchemaType = dict[str, list[str]]
"""`{'TableName': ['col1', 'col2', ...]}`"""


def sets_to_sqlite(
        flags: ScopeFlag,
        ppath: Path,
        data_objs: dict[str, Iterable[APIResource]],
        *,
        update: bool
        ) -> None:
    """
    Save sets to SQLite3 database.

    Raises
    ------
    DatabaseFileExistsError
    DatabasePathIsReservedError
    DatabaseSchemaUnmatchError
    sqlite3.DatabaseError
    """
    _validate_path(ppath, update=update)
    filing_data_attrs = Filing.get_data_attributes(
        flags, data_objs['Filing'])
    con, table_schema = _create_database_or_extend_schema(
        flags, ppath, filing_data_attrs, update=update)
    _insert_data(table_schema, data_objs, con)
    con.close()


def pages_to_sqlite(
        flags: ScopeFlag,
        ppath: Path,
        page_gen: Generator[FilingsPage, None, None],
        *,
        update: bool
        ) -> None:
    """
    Save API pages to SQLite3 database.

    Raises
    ------
    DatabaseFileExistsError
    DatabasePathIsReservedError
    DatabaseSchemaUnmatchError
    sqlite3.DatabaseError
    """
    _validate_path(ppath, update=update)
    filing_data_attrs = Filing.get_data_attributes(flags)
    con, table_schema = _create_database_or_extend_schema(
        flags, ppath, filing_data_attrs, update=update)

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


def _validate_path(ppath: Path, *, update: bool) -> None:
    """
    Validate path by raising expections.

    Raises
    ------
    DatabaseFileExistsError
        When file exists in path and `update` is `False`.
    DatabasePathIsReservedError
        When path is reserved.
    """
    if ppath.is_file():
        if not update:
            raise DatabaseFileExistsError(str(ppath))
    elif ppath.exists():
        raise DatabasePathIsReservedError(str(ppath))


def _create_database_or_extend_schema(
        flags: ScopeFlag,
        db_path: Path,
        filing_data_attrs: list[str],
        *,
        update: bool
        ) -> tuple[sqlite3.Connection, CurrentSchemaType]:
    """
    Create a new SQLite3 database or extend the database schema.

    Returns
    -------
    sqlite3.Connection
    CurrentSchemaType

    Raises
    ------
    DatabaseSchemaUnmatchError
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
            raise DatabaseSchemaUnmatchError(path)

    table_schema: CurrentSchemaType = {}
    for type_obj in resource_types:
        table_name = type_obj.__name__
        cols = data_attrs[table_name]

        col_defs = _get_col_defs(cols)
        table_schema[table_name] = [cd[0] for cd in col_defs]

        if table_name in existing_tables:
            schema_match = False
            presql = "SELECT name FROM pragma_table_info('"
            _exec(cur, f"{presql}{table_name}')")
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
                raise DatabaseSchemaUnmatchError(path)
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
            + ",\n  ".join(' '.join(cd) for cd in col_defs)
            + "\n) WITHOUT ROWID"
            )
        connection.commit()

    if options.views:
        for view in options.views:
            if view.name in existing_views:
                continue
            for table_name in view.required_tables:
                if table_name not in table_schema:
                    continue
            _exec(
                cur,
                f"CREATE VIEW {view.name}\n"
                "AS" + view.sql.rstrip()
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


def _exec(
        cur: sqlite3.Cursor,
        sql: str,
        data: list[list[str]] | None = None
        ) -> None:
    data_len = f' <count: {len(data)}>' if data else ''
    logger.debug(sql + ';' + data_len)

    if data:
        cur.executemany(sql, data)
    else:
        cur.execute(sql)


def _adapt_datetime(dt: datetime):
    try:
        fstr = time_formats[options.time_accuracy]
    except KeyError:
        fstr = time_formats['min']
    return dt.strftime(fstr)


def _adapt_list(list_in: list):
    return '\n'.join(list_in)


sqlite3.register_adapter(datetime, _adapt_datetime)
sqlite3.register_adapter(list, _adapt_list)
