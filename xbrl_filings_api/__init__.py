"""
Python API for filings.xbrl.org JSON:API by XBRL International.

The API provides an access to a repository of XBRL filings at
``filings.xbrl.org``. There are three types of API resources: filings,
entities and validation messages.

Classes
-------
Entity
    Entity objects are returned by the API and found from the `entity`
    attribute of `Filing` objects. Describes the filer.
Filing
    Filing objects are returned by the API. This is the main class of
    data.
ValidationMessage
    Validation message objects are returned by the API. Describe issues
    found by the validator software in the filings.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from .api_object.api_error import APIErrorGroup, APIError
from .api_object.entity import Entity
from .api_object.filing import Filing
from .api_object.validation_message import ValidationMessage
from .download_item import DownloadItem
from .enums import (
    ScopeFlag, GET_ONLY_FILINGS, GET_ENTITY, GET_VALIDATION_MESSAGES, NO_LIMIT)
from .exceptions import (
    FilingsAPIError, FilingsAPIErrorGroup, FilingsAPIWarning, HTTPStatusError,
    CorruptDownloadError, DatabaseFileExistsError, DatabasePathIsReservedError,
    DatabaseSchemaUnmatch, ApiReferenceWarning
    )
from .filing_set.filing_set import FilingSet
from .filing_set.resource_collection import ResourceCollection
from .filings_api import get_filings, to_sqlite
from .request_processor import api_attribute_map
from .sqlite_views import DEFAULT_VIEWS

data_attrs = [attr for attr in api_attribute_map]
