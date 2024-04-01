"""
Define query functions for filings.xbrl.org JSON:API.

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
`FILING_QUERY_ATTRS`. Please note that derived attributes such as
`reporting_date` or `language` may not be used for filtering.

To filter only the filings reported in Finland, you may use the
following parameter::

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
by a date that only has a year, 12 requests are made by default for the
end dates of each month. The months will start by default from August of
the specified year and continue until July of the year following the
specified year. Option `year_filter_months` can be used to change this
behaviour. So the following filter::

    filters={'last_end_date': 2022}

Will yield the following requests::

    last_end_date=2022-08-31
    last_end_date=2022-09-30
    ...
    last_end_date=2023-06-30
    last_end_date=2023-07-31

If you filter by a year and a month, the filter will assign the end date
of that month to the filter automatically, so
`filters={'last_end_date': '2022-12'}` becomes
`filters={'last_end_date': '2022-12-31'}`.

The parameter `sort` in functions/methods accepts a single attribute
string or a sequence (e.g. list) of attribute strings. Normal sort order
is ascending, but descending order can be obtained by prefixing the
attribute with a minus sign (-). As with filtering, attributes
ending with ``_count`` and ``_url`` did not work in July 2023.

The attributes in `FILING_QUERY_ATTRS` dict are valid values for sort.
To get the most recently added filings, specify the following
parameter::

    sort='-added_time'

.. note::
    The query functions return sets. Parameter `sort` can be used to
    filter either ends of the value spectrum but it does not mean that
    the returned sets would have any kind of order.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, Optional, Union

from xbrl_filings_api import request_processor
from xbrl_filings_api.enums import GET_ONLY_FILINGS, ScopeFlag
from xbrl_filings_api.filing_set import FilingSet
from xbrl_filings_api.filings_page import FilingsPage
from xbrl_filings_api.resource_collection import ResourceCollection


def get_filings(
        filters: Optional[Mapping[str, Union[Any, Iterable[Any]]]] = None,
        *,
        sort: Optional[Union[str, Sequence[str]]] = None,
        max_size: int = 100,
        flags: ScopeFlag = GET_ONLY_FILINGS,
        add_api_params: Optional[Mapping[str, str]] = None
        ) -> FilingSet:
    """
    Retrieve filings from the API.

    Parameters
    ----------
    filters : mapping of str: {any, iterable of any}, optional
        Mapping of filters. Iterable values may be used for AND-style
        multirequest queries. See `xbrl_filings_api.query` module
        documentation.
    sort : str or sequence of str, optional
        Used together with `max_size` to return filings from either end
        of sorted attribute values. Order is lost in `FilingSet` object.
        Default order is ascending; prefix attribute name with minus (-)
        to get descending order.
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
    filings = FilingSet()
    res_colls: dict[str, ResourceCollection] = {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }

    page_gen = request_processor.generate_pages(
        filters, max_size, flags, res_colls, sort, add_api_params)
    for page in page_gen:
        # Do not deep copy `filing_list` by using FilingSet.update
        set.update(filings, page.filing_list)
    return filings


def to_sqlite(
        path: Union[str, Path],
        *,
        update: bool = False,
        filters: Optional[Mapping[str, Union[Any, Iterable[Any]]]] = None,
        sort: Optional[Union[str, Sequence[str]]] = None,
        max_size: int = 100,
        flags: ScopeFlag = GET_ONLY_FILINGS,
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
    `False` (default), a `FileExistsError` exception will be raised. If
    `update` is `True`, retrieved records will update the existing ones
    based on `api_id` and the new ones will be added. A database to be
    updated may have additional tables and additional columns. Missing
    tables and columns will be created.

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
    update : bool, default False
        If the database already exists, update it with retrieved
        records. Old records are updated and new ones are added.
    filters : mapping of str: {any, iterable of any}, optional
        Mapping of filters. Iterable values may be used for AND-style
        multirequest queries. See `xbrl_filings_api.query` module
        documentation.
    sort : str or sequence of str, optional
        Used together with `max_size` to return filings from either end
        of sorted attribute values. Order is lost in `FilingSet` object.
        Default order is ascending; prefix attribute name with minus (-)
        to get descending order.
    max_size : int or NO_LIMIT, default 100
        Maximum number of filings to retrieve. With `NO_LIMIT`,
        you'll reach for the sky. Filings will be retrieved in
        batches (pages) of option `max_page_size`.
    flags : ScopeFlag, default GET_ONLY_FILINGS
        Scope of retrieval. Flag `GET_ENTITY` will retrieve entity
        records of filings and `GET_VALIDATION_MESSAGES` the
        validation messages.
    add_api_params: mapping, optional
        Add additional JSON:API parameters to the query. All parts
        will be URL-encoded automatically.

    Raises
    ------
    APIError
        First error returned by the filings API.
    HTTPStatusError
        If filings API does not return errors but HTTP status is not
        200.
    FileExistsError
        When ``update=False``, if the intended save path for the
        database is an existing file.
    DatabaseSchemaUnmatchError
        When ``update=True``, if the file contains a database whose
        schema does not match the expected format.
    requests.ConnectionError
        If connection fails.
    sqlite3.DatabaseError
        When ``update=True``, if the file is not a database
        (``err.sqlite_errorname='SQLITE_NOTADB'``) etc.
    """
    filings = FilingSet()
    res_colls: dict[str, ResourceCollection] = {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }

    page_gen = request_processor.generate_pages(
        filters, max_size, flags, res_colls, sort, add_api_params)
    for page in page_gen:
        page_filings = FilingSet(page.filing_list)
        page_filings.to_sqlite(
            path=path,
            update=update,
            flags=flags
            )
        # ResourceCollection reads subresource references in FilingSet
        filings.update(page_filings)
        # After database creation, next pages are always added to
        # existing db
        update = True


def filing_page_iter(
        filters: Optional[Mapping[str, Union[Any, Iterable[Any]]]] = None,
        sort: Optional[Union[str, Sequence[str]]] = None,
        max_size: int = 100,
        flags: ScopeFlag = GET_ONLY_FILINGS,
        add_api_params: Optional[Mapping[str, str]] = None
        ) -> Iterator[FilingsPage]:
    """
    Iterate API query results page by page.

    Subresources such as `Entity` are only delivered once even is
    subsequent pages contain filings that share the same entity as
    earlier pages.

    Parameters
    ----------
    filters : mapping of str: {any, iterable of any}, optional
        Mapping of filters. Iterable values may be used for AND-style
        multirequest queries. See `xbrl_filings_api.query` module
        documentation.
    sort : str or sequence of str, optional
        Used together with `max_size` to return filings from either end
        of sorted attribute values. Order is lost in `FilingSet` object.
        Default order is ascending; prefix attribute name with minus (-)
        to get descending order.
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
    filings = FilingSet()
    res_colls: dict[str, ResourceCollection] = {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }

    page_gen = request_processor.generate_pages(
        filters, max_size, flags, res_colls, sort, add_api_params)
    yield from page_gen
