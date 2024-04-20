r"""
Python API for filings.xbrl.org XBRL report repository.

The API provides an access to an international public repository of XBRL
filings. There are three types of API resources: filings, entities and
validation messages.

Modules whose contents are not exported directly are `options`, `stats`,
`debug`, and `downloader.stats`.

Classes
-------
Filing
    Filing objects are returned by the API. This is the primary resource
    class.
Entity
    Entity objects are returned by the API and found from the `entity`
    attribute of `Filing` objects. Describes the filer.
ValidationMessage
    Validation message objects are returned by the API. Describe issues
    found by the validator software in the filings.
APIError
    First error returned by the JSON:API.
FilingSet
    Set of filings returned by the query functions.
ResourceCollection
    Collection of other API resources except filings. Can be accessed
    through special attributes of `FilingSet` object.
FilingsPage
    An API page which contains predefined number of filings and other
    related resources.
DownloadInfo
DownloadItem
    Download item for a single file which overrides the values set in
    download parameters of the download function.
DownloadResult
APIObject
    Base class for all JSON-originated API objects.
APIResource
    Base class for API data object such as filings or entities.
SQLiteView
    Defines an SQL view in an SQLite database.
ScopeFlag
    Enum defining query scopes.

Constants
---------
DEFAULT_VIEWS
FILING_QUERY_ATTRS
GET_ENTITY
GET_ONLY_FILINGS
GET_VALIDATION_MESSAGES
NO_LIMIT

Functions
---------
get_filings
    Retrieve filings from the API.
to_sqlite
    Retrieve filings from the API and save them to an SQLite3 database.
filing_page_iter
    Iterate API query results page by page.
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
from xbrl_filings_api.download_info import DownloadInfo
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.downloader.download_result import DownloadResult
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import ScopeFlag
from xbrl_filings_api.exceptions import (
    CorruptDownloadError,
    DatabaseSchemaUnmatchError,
    FilingsAPIError,
    FilingsAPIWarning,
    FilterNotSupportedWarning,
    HTTPStatusError,
    JSONAPIFormatError,
)
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.filing_set import FilingSet
from xbrl_filings_api.filings_page import FilingsPage
from xbrl_filings_api.query import filing_page_iter, get_filings, to_sqlite
from xbrl_filings_api.request_processor import FILING_QUERY_ATTRS
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.sqlite_view import SQLiteView
from xbrl_filings_api.validation_message import ValidationMessage

GET_ENTITY = ScopeFlag.GET_ENTITY
GET_ONLY_FILINGS = ScopeFlag.GET_ONLY_FILINGS
GET_VALIDATION_MESSAGES = ScopeFlag.GET_VALIDATION_MESSAGES

# Do not log error and warning to standard error by default
logging.getLogger(__name__).addHandler(logging.NullHandler())
