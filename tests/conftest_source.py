"""
Configure `pytest` library.

EDITABLE: This file is the editable version of `conftest.py`. Script
``mock_upgrade.py`` must be run after editing this file (no flags, or
flag ``-n`` / ``--new``).

.. note::
    This script uses beta feature `responses._add_from_file` (as of
    `responses` version 0.23.3).
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import hashlib
from pathlib import Path
from typing import Union

import pytest
import responses  # noqa: F401

import xbrl_filings_api as xf
from xbrl_filings_api import FilingSet, ResourceCollection

MOCK_URL_DIR_NAME = 'mock_responses'

mock_dir_path = Path(__file__).parent / MOCK_URL_DIR_NAME


def _get_path(set_id):
    """Get absolute file path of the mock URL collection file."""
    file_path = mock_dir_path / f'{set_id}.yaml'
    return str(file_path)


@pytest.fixture
def filings() -> FilingSet:
    """Return FilingSet."""
    return FilingSet()


@pytest.fixture
def res_colls(filings) -> dict[str, ResourceCollection]:
    """Return subresource collections for filings fixture."""
    return {
        'Entity': filings.entities,
        'ValidationMessage': filings.validation_messages
        }


@pytest.fixture(scope='package')
def db_record_count():
    """Function for getting total count of Filing database table."""
    def _db_record_count(cur):
        cur.execute("SELECT COUNT(*) FROM Filing")
        return cur.fetchone()[0]
    return _db_record_count


@pytest.fixture(scope='module')
def mock_response_data():
    """Arbitrary data to mock download."""
    return '0123456789' * 100


@pytest.fixture(scope='module')
def mock_response_sha256(mock_response_data):
    """SHA-256 hash for `mock_response_data`."""
    fhash = hashlib.sha256(
        string=mock_response_data.encode(encoding='utf-8'),
        usedforsecurity=False
        )
    return fhash.hexdigest()


@pytest.fixture(scope='module')
def mock_url_response(mock_response_data):
    """Function to add a `responses` mock URL with `mock_response_data` body."""
    def _mock_url_response(
            url: str, rsps: Union[responses.RequestsMock, None] = None):
        nonlocal mock_response_data
        if rsps is None:
            rsps = responses
        rsps.add(
            method=responses.GET,
            url=url,
            body=mock_response_data,
            headers={}
            )
    return _mock_url_response


@pytest.fixture
def oldest3_fi_filingset(oldest3_fi_response):
    """FilingSet from mock response ``oldest3_fi``."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ONLY_FILINGS,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_entities_filingset(oldest3_fi_entities_response):
    """FilingSet from mock response ``oldest3_fi_entities`` with entities."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ENTITY,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_vmessages_filingset(oldest3_fi_vmessages_response):
    """FilingSet from mock response ``oldest3_fi_vmessages`` with validation messages."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_VALIDATION_MESSAGES,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_ent_vmessages_filingset(oldest3_fi_ent_vmessages_response):
    """FilingSet from mock response ``oldest3_fi_ent_vmessages`` with entities and validation messages."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES),
        add_api_params=None
        )
