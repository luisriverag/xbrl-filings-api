"""
Configure `pytest` library.

EDITABLE: This file is the editable version of `conftest.py`. Script
``mock_upgrade.py`` must be run after editing this file (no flags, or
flag ``-n`` / ``--new``).

.. note::
    Fixture method `urlmock.apply` uses beta feature
    `responses._add_from_file` (as of `responses` version 0.23.3).
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import hashlib
import re
from datetime import datetime, timezone
from typing import Union

import pytest
import responses

import xbrl_filings_api as xf
from tests.urlmock import UrlMock
from xbrl_filings_api import FilingSet, ResourceCollection
from xbrl_filings_api.api_request import _APIRequest

UTC = timezone.utc

MOCK_URL_DIR_NAME = 'mock_responses'


@pytest.fixture(scope='package')
def urlmock() -> UrlMock:
    """
    Define operations for URL mock responses.

    Methods
    -------
    path
        Get absolute file path of the mock URL response file.
    apply
        Apply the mock URL response on the test for requests library.
    """
    instance = UrlMock()
    return instance


@pytest.fixture
def filings() -> FilingSet:
    """Empty FilingSet."""
    return FilingSet()


@pytest.fixture
def res_colls(filings) -> dict[str, ResourceCollection]:
    """Subresource collections as dict, keyed with class names."""
    return {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }


@pytest.fixture(scope='package')
def db_record_count():
    """Get total count of database records in Filing table."""
    def _db_record_count(cur):
        cur.execute("SELECT COUNT(*) FROM Filing")
        return cur.fetchone()[0]
    return _db_record_count


@pytest.fixture(scope='module')
def mock_response_data():
    """Arbitrary data for mock download, 1000 chars."""
    return '0123456789' * 100


@pytest.fixture(scope='module')
def mock_response_sha256(mock_response_data):
    """SHA-256 hash for fixture mock_response_data."""
    fhash = hashlib.sha256(
        string=mock_response_data.encode(encoding='utf-8'),
        usedforsecurity=False
        )
    return fhash.hexdigest()


@pytest.fixture(scope='module')
def mock_url_response(mock_response_data):
    """Add a `responses` mock URL with fixt mock_response_data body."""
    def _mock_url_response(
            url: str, rsps: Union[responses.RequestsMock, None] = None):
        if rsps is None:
            rsps = responses
        rsps.add(
            method=responses.GET,
            url=url,
            body=mock_response_data,
            headers={}
            )
    return _mock_url_response


@pytest.fixture(scope='package')
def get_oldest3_fi_filingset(urlmock):
    """Get FilingSet from mock response oldest3_fi."""
    def _get_oldest3_fi_filingset():
        fs = None
        with responses.RequestsMock() as rsps:
            urlmock.apply(rsps, 'oldest3_fi')
            fs = xf.get_filings(
                filters={'country': 'FI'},
                sort='date_added',
                limit=3,
                flags=xf.GET_ONLY_FILINGS,
                add_api_params=None
                )
        return fs
    return _get_oldest3_fi_filingset


@pytest.fixture(scope='package')
def get_oldest3_fi_entities_filingset(urlmock):
    """Get FilingSet from mock response oldest3_fi_entities."""
    def _get_oldest3_fi_entities_filingset():
        fs = None
        with responses.RequestsMock() as rsps:
            urlmock.apply(rsps, 'oldest3_fi_entities')
            fs = xf.get_filings(
                filters={'country': 'FI'},
                sort='date_added',
                limit=3,
                flags=xf.GET_ENTITY,
                add_api_params=None
                )
        return fs
    return _get_oldest3_fi_entities_filingset


@pytest.fixture(scope='package')
def get_oldest3_fi_vmessages_filingset(urlmock):
    """Get FilingSet from mock response oldest3_fi_vmessages."""
    def _get_oldest3_fi_vmessages_filingset():
        fs = None
        with responses.RequestsMock() as rsps:
            urlmock.apply(rsps, 'oldest3_fi_vmessages')
            fs = xf.get_filings(
                filters={'country': 'FI'},
                sort='date_added',
                limit=3,
                flags=xf.GET_VALIDATION_MESSAGES,
                add_api_params=None
                )
        return fs
    return _get_oldest3_fi_vmessages_filingset


@pytest.fixture(scope='package')
def get_oldest3_fi_ent_vmessages_filingset(urlmock):
    """Get FilingSet from mock response ``oldest3_fi_ent_vmessages``."""
    def _get_oldest3_fi_ent_vmessages_filingset():
        fs = None
        with responses.RequestsMock() as rsps:
            urlmock.apply(rsps, 'oldest3_fi_ent_vmessages')
            fs = xf.get_filings(
                filters={'country': 'FI'},
                sort='date_added',
                limit=3,
                flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES),
                add_api_params=None
                )
        return fs
    return _get_oldest3_fi_ent_vmessages_filingset


@pytest.fixture(scope='package')
def dummy_api_request():
    """Dummy _APIRequest object."""
    return _APIRequest(
        'https://filings.xbrl.org/api/filings?Dummy=Url',
        query_time=datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)
        )


@pytest.fixture(scope='session', autouse=True)
def all_test_functions(request):
    """All test functions in a dict with access paths as keys."""
    test_funcs = {}
    session = request.node
    for item in session.items:
        func_obj = item.getparent(pytest.Function)
        func = func_obj.function
        fname = (
            f'{func.__module__}.'
            + re.sub(r'\[.*\]', '', func_obj.name)
            )
        test_funcs[fname] = func
    return test_funcs
