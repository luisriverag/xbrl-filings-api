"""
Python API for filings.xbrl.org XBRL report repository.

The API provides an access to an international public repository of XBRL
filings. There are three types of API resources: filings, entities and
validation messages.

Modules whose contents are not exported directly are `options`, `stats`,
`debug`, and `downloader.stats`.

Constants
---------
DEFAULT_VIEWS
    List of the default views added to exported SQLite databases.
FILING_QUERY_ATTRS
    List of resource attribute names for parameters sort and filter.
GET_ENTITY
    Retrieve entities of filings.
GET_ONLY_FILINGS
    Retrieve only filings and nothing else. Overrides other flags.
GET_VALIDATION_MESSAGES
    Retrieve validation messages of filings.
NO_LIMIT
    Fetches all filings that match the query.

Functions
---------
get_filings
    Return a FilingSet of all the filings matching the query.
to_sqlite
    Insert all filings from the query to an SQLite database.
filing_page_iter
    Lazily iterate query results page by page.

Classes
-------
Filing
    XBRL filing in the database based on a report package.
Entity
    Entity (e.g. a group) in the database which has filed filings.
ValidationMessage
    Message for a filing in the database from a validator software.
FilingSet
    Subclassed :class:`set` for `Filing` objects.
ResourceCollection
    Collection of subresources of a `FilingSet` object.
FilingsPage
    Response page containing filings as primary resource.
DownloadInfo
    Dataclass for attribute DownloadSpecs.info.
DownloadItem
    Dataclass defining download item for download functions.
DownloadResult
    Dataclass for result information from a finished download.
APIObject
    Base class for JSON:API objects.
APIResource
    Base class for JSON:API resources, i.e., data objects.
SQLiteView
    Dataclass for storing SQLite view creation instructions.
ScopeFlag
    Flags for API resource retrieval scope.

Exceptions
----------
APIError
    First error returned by the JSON:API.
CorruptDownloadError
    SHA-256 checksum does not match expected value from API.
DatabaseSchemaUnmatchError
    The file contains a database whose schema is non-conformant.
FilingsAPIError
    Base class for exceptions in this library.
FilingsAPIWarning
    Base class for warnings in this library.
FilterNotSupportedWarning
    Used filter is not supported but can be used.
HTTPStatusError
    No APIError but the HTTP status is not 200.
JSONAPIFormatError
    The API returns a JSON:API document in bad format.
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
