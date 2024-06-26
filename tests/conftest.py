"""
Configure `pytest` library.

DO NOT EDIT: This module is automatically generated by the script
``mock_upgrade.py``. Edit file ``conftest_source.py`` instead and run
the aforementioned script.

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
from xbrl_filings_api.api_request import APIRequest

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
    """Dummy APIRequest object."""
    return APIRequest(
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


@pytest.fixture
def creditsuisse21en_by_id_response(urlmock):
    """Credit Suisse 2021 English AFR filing by `api_id`."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'creditsuisse21en_by_id')
        yield rsps


@pytest.fixture
def creditsuisse21en_by_id_entity_response(urlmock):
    """
    Credit Suisse 2021 English AFR filing by `api_id` and with Entity.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'creditsuisse21en_by_id_entity')
        yield rsps


@pytest.fixture
def asml22en_response(urlmock):
    """ASML Holding 2022 English AFR filing."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'asml22en')
        yield rsps


@pytest.fixture
def asml22en_entities_response(urlmock):
    """ASML Holding 2022 English AFR filing with entity."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'asml22en_entities')
        yield rsps


@pytest.fixture
def asml22en_vmessages_response(urlmock):
    """ASML Holding 2022 English AFR filing with validation messages."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'asml22en_vmessages')
        yield rsps


@pytest.fixture
def assicurazioni21it_vmessages_response(urlmock):
    """
    Assicurazioni Generali 2021 Italian AFR filing with validation
    messages.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'assicurazioni21it_vmessages')
        yield rsps


@pytest.fixture
def tecnotree21fi_vmessages_response(urlmock):
    """Tecnotree 2021 Finnish AFR filing with validation messages."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'tecnotree21fi_vmessages')
        yield rsps


@pytest.fixture
def asml22en_ent_vmsg_response(urlmock):
    """
    ASML Holding 2022 English AFR filing with entities and v-messages.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'asml22en_ent_vmsg')
        yield rsps


@pytest.fixture
def filter_language_response(urlmock):
    """Filter by language 'fi'."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_language')
        yield rsps


@pytest.fixture
def filter_last_end_date_response(urlmock):
    """Filter by last_end_date '2021-02-28'."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_last_end_date')
        yield rsps


@pytest.fixture
def filter_last_end_date_lax_response(urlmock):
    """Filter by last_end_date '2021-02-28'."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        urlmock.apply(rsps, 'filter_last_end_date')
        yield rsps


@pytest.fixture
def filter_error_count_response(urlmock):
    """Filter by error_count value 0."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_error_count')
        yield rsps


@pytest.fixture
def filter_inconsistency_count_response(urlmock):
    """Filter by `inconsistency_count` value 0."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_inconsistency_count')
        yield rsps


@pytest.fixture
def filter_warning_count_response(urlmock):
    """Filter by warning_count value 0."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_warning_count')
        yield rsps


@pytest.fixture
def filter_added_time_response(urlmock):
    """Filter by added_time value '2021-09-23 00:00:00'."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_added_time')
        yield rsps


@pytest.fixture
def filter_added_time_lax_response(urlmock):
    """Filter by added_time value '2021-09-23 00:00:00'."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        urlmock.apply(rsps, 'filter_added_time')
        yield rsps


@pytest.fixture
def filter_added_time_2_response(urlmock):
    """Filter by added_time value '2023-05-09 13:27:02.676029'."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_added_time_2')
        yield rsps


@pytest.fixture
def filter_entity_api_id_response(urlmock):
    """Return error when filtering with `entity_api_id`."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_entity_api_id')
        yield rsps


@pytest.fixture
def filter_entity_api_id_lax_response(urlmock):
    """Return error when filtering with `entity_api_id`."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        urlmock.apply(rsps, 'filter_entity_api_id')
        yield rsps


@pytest.fixture
def filter_json_url_response(urlmock):
    """Filter by json_url of Kone 2022 [en] filing."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_json_url')
        yield rsps


@pytest.fixture
def filter_package_url_response(urlmock):
    """Filter by package_url of Kone 2022 [en] filing."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_package_url')
        yield rsps


@pytest.fixture
def filter_viewer_url_response(urlmock):
    """Filter by viewer_url of Kone 2022 [en] filing."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_viewer_url')
        yield rsps


@pytest.fixture
def filter_xhtml_url_response(urlmock):
    """Filter by xhtml_url of Kone 2022 [en] filing."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_xhtml_url')
        yield rsps


@pytest.fixture
def filter_package_sha256_response(urlmock):
    """Filter by package_sha256 of Kone 2022 filing."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'filter_package_sha256')
        yield rsps


@pytest.fixture
def finnish_jan22_response(urlmock):
    """Finnish AFR filings with reporting period ending in Jan 2022."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'finnish_jan22')
        yield rsps


@pytest.fixture
def oldest3_fi_response(urlmock):
    """Oldest 3 AFR filings reported in Finland."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'oldest3_fi')
        yield rsps


@pytest.fixture
def oldest3_fi_entities_response(urlmock):
    """Oldest 3 AFR filings reported in Finland with entities."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'oldest3_fi_entities')
        yield rsps


@pytest.fixture
def oldest3_fi_vmessages_response(urlmock):
    """
    Oldest 3 AFR filings reported in Finland with validation messages.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'oldest3_fi_vmessages')
        yield rsps


@pytest.fixture
def oldest3_fi_ent_vmessages_response(urlmock):
    """
    Oldest 3 AFR filings reported in Finland with entities and
    validation messages.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'oldest3_fi_ent_vmessages')
        yield rsps


@pytest.fixture
def sort_two_fields_response(urlmock):
    """
    Sort Finnish filings by `last_end_date` and `added_time`. WARNING,
    volatile with ``mock_upgrade.py`` run. See test
    ``test_query_sort::test_sort_two_fields``.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'sort_two_fields')
        yield rsps


@pytest.fixture
def paging_swedish_size2_pg3_response(urlmock):
    """
    Get 3 pages, actually 4, (pg size 2) of oldest Swedish filings.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'paging_swedish_size2_pg3')
        yield rsps


@pytest.fixture
def paging_swedish_size2_pg3_lax_response(urlmock):
    """
    Get 3 pages, actually 4, (pg size 2) of oldest Swedish filings.
    """
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        urlmock.apply(rsps, 'paging_swedish_size2_pg3')
        yield rsps


@pytest.fixture
def paging_oldest_ukrainian_2pg_4ea_response(urlmock):
    """Get oldest Ukrainian filings 2 pages, 4 filings each."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'paging_oldest_ukrainian_2pg_4ea')
        yield rsps


@pytest.fixture
def multifilter_api_id_response(urlmock):
    """Get 4 Shell filings for 2021 and 2022."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_api_id')
        yield rsps


@pytest.fixture
def multifilter_api_id_entities_response(urlmock):
    """Get 4 Shell filings for 2021 and 2022 with entities."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_api_id_entities')
        yield rsps


@pytest.fixture
def multifilter_country_response(urlmock):
    """Get three filings for the country `FI`."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_country')
        yield rsps


@pytest.fixture
def multifilter_filing_index_response(urlmock):
    """Get both Shell 2021 filings filtered with filing_index."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_filing_index')
        yield rsps


@pytest.fixture
def multifilter_reporting_date_response(urlmock):
    """Return an error for filtering with `reporting_date`."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_reporting_date')
        yield rsps


@pytest.fixture
def multifilter_processed_time_response(urlmock):
    """Get two filings filtered with `processed_time`."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_processed_time')
        yield rsps


@pytest.fixture
def unknown_filter_error_response(urlmock):
    """Get an error of unknown filter."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'unknown_filter_error')
        yield rsps


@pytest.fixture
def bad_page_error_response(urlmock):
    """Get an error of page number -1."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'bad_page_error')
        yield rsps


@pytest.fixture
def fortum23fi_xhtml_language_response(urlmock):
    """Fortum 2023 Finnish AFR filing with language in xhtml_url."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'fortum23fi_xhtml_language')
        yield rsps


@pytest.fixture
def paging_czechia20dec_response(urlmock):
    """Czech 2020-12-31 AFRs."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'paging_czechia20dec')
        yield rsps


@pytest.fixture
def multifilter_belgium20_short_date_year_response(urlmock):
    """
    Belgian 2020 AFRs querying with short date filter year,
    limit=100.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_belgium20_short_date_year')
        yield rsps


@pytest.fixture
def multifilter_belgium20_short_date_year_no_limit_response(urlmock):
    """
    Belgian 2020 AFRs querying with short date filter year,
    limit=NO_LIMIT, options.max_page_size=200.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'multifilter_belgium20_short_date_year_no_limit')
        yield rsps


@pytest.fixture
def sort_asc_package_sha256_latvia_response(urlmock):
    """Sorted ascending by package_sha256 from Latvian records."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'sort_asc_package_sha256_latvia')
        yield rsps


@pytest.fixture
def sort_desc_package_sha256_latvia_response(urlmock):
    """Sorted ascending by package_sha256 from Latvian records."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'sort_desc_package_sha256_latvia')
        yield rsps


@pytest.fixture
def kone22_all_languages_response(urlmock):
    """Sorted ascending by package_sha256 from Latvian records."""
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'kone22_all_languages')
        yield rsps


@pytest.fixture
def estonian_2_pages_3_each_response(urlmock):
    """
    Estonian filings 2 pages of size 3, incl. entities, v-messages.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'estonian_2_pages_3_each')
        yield rsps


@pytest.fixture
def ageas21_22_response(urlmock):
    """
    Ageas 2021 and 2022 filings in 3 languages (nl, fr, en) with
    entities, 6 filings.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'ageas21_22')
        yield rsps


@pytest.fixture
def applus20_21_response(urlmock):
    """
    Applus Services 2020, 2021 filings with entities, 2 filings, same
    last_end_date.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'applus20_21')
        yield rsps


@pytest.fixture
def upm21to22_response(urlmock):
    """
    UPM-Kymmene 2021 to 2022 filings (en, fi) with entities, 4 filings.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'upm21to22')
        yield rsps


@pytest.fixture
def upm22to23_response(urlmock):
    """
    UPM-Kymmene 2022 to 2023 filings (en, fi) with entities, 4 filings.
    """
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'upm22to23')
        yield rsps
