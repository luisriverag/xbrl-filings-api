"""
Configuration of `pytest` library.

.. note::
    This script uses beta feature `responses._add_from_file` (as of
    `responses` version 0.23.3).
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
import responses

MOCK_URL_DIR_NAME = 'mock_responses'

mock_dir_path = Path(__file__).parent / MOCK_URL_DIR_NAME


def _get_absolute_path(set_id):
    file_path = mock_dir_path / f'{set_id}.yaml'
    return str(file_path)


@pytest.fixture
def creditsuisse21en_by_id_response():
    """Credit Suisse 2021 English AFR filing by `api_id`."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('creditsuisse21en_by_id'))
        yield rsps


@pytest.fixture
def asml22en_response():
    """ASML Holding 2022 English AFR filing."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('asml22en'))
        yield rsps


@pytest.fixture
def asml22en_entities_response():
    """ASML Holding 2022 English AFR filing with entity."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('asml22en_entities'))
        yield rsps


@pytest.fixture
def asml22en_vmessages_response():
    """ASML Holding 2022 English AFR filing with validation messages."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('asml22en_vmessages'))
        yield rsps


@pytest.fixture
def asml22en_ent_vmsg_response():
    """ASML Holding 2022 English AFR filing with entities and v-messages."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('asml22en_ent_vmsg'))
        yield rsps


@pytest.fixture
def filter_language_response():
    """Filter by language 'fi'."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('filter_language'))
        yield rsps


@pytest.fixture
def filter_last_end_date_response():
    """Filter by last_end_date '2021-02-28'."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('filter_last_end_date'))
        yield rsps


@pytest.fixture
def filter_error_count_response():
    """Filter by error_count value 1."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('filter_error_count'))
        yield rsps


@pytest.fixture
def finnish_jan22_response():
    """Finnish AFR filings with reporting period ending in Jan 2022."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('finnish_jan22'))
        yield rsps


@pytest.fixture
def oldest3_fi_response():
    """Oldest 3 AFR filings reported in Finland."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('oldest3_fi'))
        yield rsps


@pytest.fixture
def sort_two_fields_response():
    """
    Sort Finnish filings by `last_end_date` and `added_time`.

    .. warning::

        Volatile with ``mock_upgrade.py`` run. See test
        ``test_query::Test_get_filings::test_sort_two_fields``.
    """
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('sort_two_fields'))
        yield rsps


@pytest.fixture
def multipage_response():
    """Get 3 pages (2pc) of oldest Swedish filings."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('multipage'))
        yield rsps


@pytest.fixture
def multipage_xfail_response():
    """Get 3 pages (2pc) of oldest Swedish filings."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps._add_from_file(_get_absolute_path('multipage'))
        yield rsps
