"""
Python API for filings.xbrl.org JSON:API by XBRL International.

The API provides an access to a repository of XBRL filings at
``filings.xbrl.org``. There are three types of API resources: filings,
entities and validation messages.

Classes
-------
APIError
    First error returned by the JSON:API.
APIObject
    Base class for all JSON-originated API objects.
APIResource
    Base class for API data object such as filings or entities.
DownloadItem
    Download item for a single file which overrides the values set in
    download parameters of the download function.
DownloadResult
    Information on the result of a single download.
Entity
    Entity objects are returned by the API and found from the `entity`
    attribute of `Filing` objects. Describes the filer.
Filing
    Filing objects are returned by the API. This is the primary resource
    class.
FilingSet
    Set of filings returned by the query functions.
FilingsPage
    An API page which contains predefined number of filings and other
    related resources.
ResourceCollection
    Collection of other API resources except filings. Can be accessed
    through special attributes of `FilingSet` object.
ScopeFlag
    Enum defining query scopes.
SQLiteView
    Defines an SQL view in an SQLite database.
ValidationMessage
    Validation message objects are returned by the API. Describe issues
    found by the validator software in the filings.

Constants
---------
DEFAULT_VIEWS
    Library-defined SQLite views for the exported database.
FILING_QUERY_ATTRS
    List of resource attribute names for `sort` and `filter` parameters
    of filing queries. Does not include derived attributes.
GET_ENTITY
    Request entities of filings in a query. A member of enum
    `ScopeFlag`.
GET_ONLY_FILINGS
    Request nothing but filings. Overrides all other flags. A member of
    enum `ScopeFlag`.
GET_VALIDATION_MESSAGES
    Request validation messages of filings. A member of enum
    `ScopeFlag`.
NO_LIMIT
    Drain the query completely when set to `max_size` parameter.

Functions
---------
filing_page_iter
    Iterate API query results page by page.
get_filings
    Retrieve filings from the API.
to_sqlite
    Retrieve filings from the API and save them to an SQLite3 database.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging

from xbrl_filings_api.api_error import APIError
from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import NO_LIMIT
from xbrl_filings_api.default_views import DEFAULT_VIEWS
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.downloader.download_result import DownloadResult
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    ScopeFlag,
)
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.filing_set import FilingSet
from xbrl_filings_api.filings_page import FilingsPage
from xbrl_filings_api.query import filing_page_iter, get_filings, to_sqlite
from xbrl_filings_api.request_processor import FILING_QUERY_ATTRS
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.sqlite_view import SQLiteView
from xbrl_filings_api.validation_message import ValidationMessage

# Do not log error and warning to standard error by default
logging.getLogger(__name__).addHandler(logging.NullHandler())
