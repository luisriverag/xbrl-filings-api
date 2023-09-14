"""
Python API for filings.xbrl.org JSON:API by XBRL International.

The API provides an access to a repository of XBRL filings at
``filings.xbrl.org``. There are three types of API resources:
filings, entities and validation messages.

The parameter `filters` in functions/methods accepts a mapping such as a
dictionary. Key is the attribute being searched for and the value is
the searched item or an iterable of searched items. Both attribute
styles are supported: the ones used by this library and the actual
attribute names in the API. Search is case-sensitive. The API only
supports equivalence filtering of one value, but by giving the
mapping a value which is an iterable of strings, you may execute
multiple equivalence filtering queries in one function/method call.

You will find the list of valid filtering attributes in list
`FILTER_ATTRS`. Please note
that derived attributes such as `reporting_date` or `language` may
not be used for filtering.

Note however that as of July 2023, attributes ending with ``_count``
and ``_url`` could not be used. To filter only the filings reported
in Finland, you may use the following parameter::

    filters={'country': 'FI'}

To filter reports of Finnish companies Apetit and Boreo, the most
reliable way is to filter them using their LEI codes which are
defined in the entity `identifier` attribute::

    filters={'entity.identifier': [
                '743700RSFZUIQYABYT14',
                '743700OD4QRWKZ4ODC98']}

For validation messages, plural prefix `validation_messages.` is
required:

    filters={
        'validation_messages.code': 'message:tech_duplicated_facts1'
        }

Date fields have a special functioning in `filters`. If you filter
by a date that only has a year, a minimum of 12 requests are made
for the end dates of each month. The months will start by default
from August of the specified year and continue until July of the
year following the specified year. Option `year_filter_months` can
be used to change this behaviour. If you filter by a year and a
month, the filter will assign the end date of that month to the
filter automatically. So the following filter::

    filters={'last_end_date': '2022'}

Will yield the following requests::

    last_end_date=2022-08-31
    last_end_date=2022-09-30
    ...
    last_end_date=2023-06-30
    last_end_date=2023-07-31

The parameter `sort` in functions/methods accepts a single attribute
string or a sequence (e.g. list) of attribute strings. Normal sort order
is ascending, but descending order can be obtained by prefixing the
attribute with a minus sign (-). As with filtering, attributes
ending with ``_count`` and ``_url`` did not work in July 2023. The
same keys of `api_attributes` dict are valid values for sort. To get
the most recently added filings, specify the following parameter::

    sort='-added_time'

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Optional

from xbrl_filings_api import request_processor
from xbrl_filings_api.enums import GET_ONLY_FILINGS, ScopeFlag
from xbrl_filings_api.filing_set import FilingSet
from xbrl_filings_api.filings_page import FilingsPage
from xbrl_filings_api.resource_collection import ResourceCollection


def get_filings(
        filters: Optional[Mapping[str, Any | Iterable[Any]]] = None,
        *,
        sort: Optional[str | Sequence[str]] = None,
        max_size: int = 100,
        flags: ScopeFlag = GET_ONLY_FILINGS,
        add_api_params: Optional[Mapping[str, str]] = None
        ) -> FilingSet:
    """
    Retrieve filings from the API.

    Parameters
    ----------
    filters : mapping of str: {any, iterable of any}, optional
        Mapping of filters. See `FilingAPI` class documentation.
    sort : str or sequence of str, optional
        Sort result set by specified attribute(s). Use values of
        `FILTER_ATTRS`. Descending order field begins with minus sign (-).
    max_size : int or NO_LIMIT, default 100
        Maximum number of filings to retrieve. With `NO_LIMIT`,
        you'll reach for the sky. Filings will be retrieved in
        batches (pages) of option `max_page_size`.
    flags : ScopeFlag, default GET_ONLY_FILINGS
        Scope of retrieval. Flag `GET_ENTITY` will retrieve and
        create the object for `filing.entity` and
        `GET_VALIDATION_MESSAGES` a set of objects for
        `filing.validation_messages`.
    add_api_params: mapping, optional
        Add additional JSON:API parameters to the query. All parts
        will be URL-encoded automatically.

    Returns
    -------
    FilingSet of Filing
        Set of retrieved filings.
    """
    if isinstance(sort, str):
        sort = [sort]

    filings = FilingSet({})
    res_colls: dict[str, ResourceCollection] = {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }

    page_gen = request_processor.generate_pages(
        filters, sort, max_size, flags, add_api_params, res_colls)
    for page in page_gen:
        filings.update(page.filing_list)
    return filings


def to_sqlite(
        path: str | Path,
        flags: ScopeFlag = GET_ONLY_FILINGS,
        *,
        update: bool = False,
        filters: Optional[Mapping[str, Any | Iterable[Any]]] = None,
        sort: Optional[str | Sequence[str]] = None,
        max_size: int = 100,
        add_api_params: Optional[Mapping[str, str]] = None
        ) -> None:
    """
    Retrieve filings from the API and save them to an SQLite3 database.

    Tables ``Filing``, ``Entity`` and ``ValidationMessage`` will be
    created according to settings in `flags`. Dependencies for SQL
    joins:
        * ``Filing.entity_api_id = Entity.api_id``
        * ``Filing.api_id = ValidationMessage.filing_api_id``

    If a file exists in `path` parameter path and `update` is
    `False` (default), a `DatabaseFileExistsError` exception will be
    raised. If `update` is `True`, retrieved records will update the
    existing ones based on `api_id` and the new ones will be added.
    A database to be updated may have additional tables and
    additional columns. Missing tables and columns will be created.

    If the intermediary folders in `path` do not exist, they will be
    created.

    If `update` is `True` and the database does not have any
    expected tables defined or any of the expected tables contain no
    expected columns, a `DatabaseSchemaUnmatchError` exception will be
    raised.

    The parameter `add_api_params` can be used to override
    automatically generated JSON:API parameters ``page[size]``,
    ``include`` and ``filter[<field>]`` and to add more of them to
    the query.

    Parameters
    ----------
    path : str or Path
        Path to the SQLite database.
    flags : ScopeFlag, default GET_ONLY_FILINGS
        Scope of retrieval. Flag `GET_ENTITY` will retrieve entity
        records of filings and `GET_VALIDATION_MESSAGES` the
        validation messages.
    update : bool, default False
        If the database already exists, update it with retrieved
        records. Old records are updated and new ones are added.
    filters : mapping of str: {any, iterable of any}, optional
        Mapping of filters. See `FilingAPI` class documentation.
    sort : str or sequence of str, optional
        Sort result set by specified attribute(s). Use values of
        `FILTER_ATTRS`. Descending order field begins with minus sign (-).
    max_size : int or NO_LIMIT, default 100
        Maximum number of filings to retrieve. With `NO_LIMIT`,
        you'll reach for the sky. Filings will be retrieved in
        batches (pages) of option `max_page_size`.
    add_api_params: mapping, optional
        Add additional JSON:API parameters to the query. All parts
        will be URL-encoded automatically.

    Raises
    ------
    APIErrorGroup of APIError
        If filings API returns errors.
    HTTPStatusError
        If filings API does not return errors but HTTP status is not
        200.
    DatabaseFileExistsError
        When ``update=False``, if the intended save path for the
        database is an existing file.
    DatabasePathIsReservedError
        The intended save path for the database is already reserved
        by a non-file database object.
    DatabaseSchemaUnmatchError
        When ``update=True``, if the file contains a database whose
        schema does not match the expected format.
    requests.ConnectionError
        If connection fails.
    sqlite3.DatabaseError
        When ``update=True``, if the file is not a database
        (``err.sqlite_errorname='SQLITE_NOTADB'``) etc.
    """
    if isinstance(sort, str):
        sort = [sort]

    filings = FilingSet({})
    res_colls: dict[str, ResourceCollection] = {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }

    page_gen = request_processor.generate_pages(
        filters, sort, max_size, flags, add_api_params, res_colls)
    for page in page_gen:
        FilingSet(page.filing_list).to_sqlite(path, flags, update=update)
        filings.update(page.filing_list)


def filing_page_iter(
        filters: Optional[Mapping[str, Any | Iterable[Any]]] = None,
        sort: Optional[str | Sequence[str]] = None,
        max_size: int = 100,
        flags: ScopeFlag = GET_ONLY_FILINGS,
        add_api_params: Optional[Mapping[str, str]] = None
        ) -> Iterator[FilingsPage]:
    """
    Iterate API query results page by page.

    Parameters
    ----------
    filters : mapping of str: {any, iterable of any}, optional
        Mapping of filters. See `FilingAPI` class documentation.
    sort : str or sequence of str, optional
        Sort result set by specified attribute(s). Use values of
        `FILTER_ATTRS`. Descending order field begins with minus sign (-).
    max_size : int or NO_LIMIT, default 100
        Maximum number of filings to retrieve. With `NO_LIMIT`,
        you'll reach for the sky. Filings will be retrieved in
        batches (pages) of option `max_page_size`.
    flags : ScopeFlag, default GET_ONLY_FILINGS
        Scope of retrieval. Flag `GET_ENTITY` will retrieve and
        create the object for `filing.entity` and
        `GET_VALIDATION_MESSAGES` a set of objects for
        `filing.validation_messages`.
    add_api_params: mapping, optional
        Add additional JSON:API parameters to the query. All parts
        will be URL-encoded automatically.

    Yields
    ------
    FilingsPage
        Filings page containing a batch of downloaded filings
    """
    if isinstance(sort, str):
        sort = [sort]

    filings = FilingSet({})
    res_colls: dict[str, ResourceCollection] = {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }

    page_gen = request_processor.generate_pages(
        filters, sort, max_size, flags, add_api_params, res_colls)
    yield from page_gen
