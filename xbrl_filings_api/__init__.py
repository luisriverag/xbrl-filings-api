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

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging

from xbrl_filings_api.api_error import APIError, APIErrorGroup
from xbrl_filings_api.default_views import DEFAULT_VIEWS
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.entity import Entity
from xbrl_filings_api.enums import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    NO_LIMIT,
    ScopeFlag,
)
from xbrl_filings_api.exceptions import (
    CorruptDownloadError,
    DatabaseFileExistsError,
    DatabasePathIsReservedError,
    DatabaseSchemaUnmatchError,
    FilingsAPIError,
    FilingsAPIErrorGroup,
    FilingsAPIWarning,
    HTTPStatusError,
)
from xbrl_filings_api.filing_set import FilingSet
from xbrl_filings_api.filings_api import get_filings, to_sqlite
from xbrl_filings_api.request_processor import api_attribute_map
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.validation_message import ValidationMessage

data_attrs = list(api_attribute_map)
logging.getLogger(__name__).addHandler(logging.NullHandler())
