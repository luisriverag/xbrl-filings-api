"""
Fetch mock URLs for tests and save them.

This module is a standalone script and it is not available for
importing.

The fetched URLs will be saved to YAML files in directory
`MOCK_URL_DIR_NAME` inside `tests` package.

.. note::
    This script uses beta feature `responses._recorder` (as of
    `responses` version 0.23.3).
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import argparse
import re
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests
from responses import _recorder
from urlmock import UrlMock

MOCK_URL_DIR_NAME = 'mock_responses'
CONFTEST_SRC_PATH = 'conftest_source.py'
CONFTEST_OUT_PATH = 'conftest.py'
ENTRY_POINT_URL = 'https://filings.xbrl.org/api/filings'
REQUEST_TIMEOUT = 30.0

conftest_src_spath = str(Path(__file__).parent / CONFTEST_SRC_PATH)
conftest_out_spath = str(Path(__file__).parent / CONFTEST_OUT_PATH)
mock_dir_path = Path(__file__).parent / MOCK_URL_DIR_NAME
JSON_API_HEADERS = {
    'Content-Type': 'application/vnd.api+json'
    }
REMOVE_UNNECESSARY_IMPORT_NOQA_MODULES = ('responses',)
NOQA_PATTERN = 'import {module_name}  # noqa: F401\n'
remove_unnecessary_import_noqa_lines = tuple(
    NOQA_PATTERN.format(module_name=module_name)
    for module_name in REMOVE_UNNECESSARY_IMPORT_NOQA_MODULES
    )

URL_MOCK_FIXTURE_TEMPLATE = '''
@pytest.fixture
def {fixt_name}_response(urlmock):
    """{docstring}"""
    with responses.RequestsMock({param_str}) as rsps:
        urlmock.apply(rsps, '{name}')
        yield rsps
'''
URL_MOCK_PARAM_LAX = 'assert_all_requests_are_fired=False'
NO_EDIT_DOCSTRING = '''
DO NOT EDIT: This module is automatically generated by the script
``mock_upgrade.py``. Edit file ``conftest_source.py`` instead and run
the aforementioned script.
'''

urlmock = UrlMock()
urlmock_defs = {}


@dataclass
class _URLMockDefinition:
    name: str
    """Name of the mock URL collection."""
    fetch: Callable
    """Function to fetch and save the URL mock collection."""
    lax_fixture: bool
    """
    Also create a fixture with a name ``<name>_lax``.

    The lax version of the fixture adds parameter
    ``assert_all_requests_are_fired=False`` to initiation of
    `responses.RequestsMock`. These fixtures are used when the test
    function should raise (other than APIError) and not necessarily
    initiate all of the URL request.
    """
    isfetch: bool = True
    """Should this mock be fetched."""


def _addmock(name, lax_fixture=False):  # noqa: FBT002
    urlmock_defs[name] = _URLMockDefinition(
        name=name,
        fetch=globals()[f'_fetch_{name}'],
        lax_fixture=lax_fixture
        )


###################### DEFINE MOCK URL COLLECTIONS #####################


@_recorder.record(file_path=urlmock.path('creditsuisse21en_by_id'))
def _fetch_creditsuisse21en_by_id():
    """Credit Suisse 2021 English AFR filing by `api_id`."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            # id = api_id
            'filter[id]': '162',
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('creditsuisse21en_by_id')


@_recorder.record(file_path=urlmock.path('creditsuisse21en_by_id_entity'))
def _fetch_creditsuisse21en_by_id_entity():
    """
    Credit Suisse 2021 English AFR filing by `api_id` and with Entity.
    """
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            # id = api_id
            'filter[id]': '162',
            'include': 'entity',
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('creditsuisse21en_by_id_entity')


@_recorder.record(file_path=urlmock.path('asml22en'))
def _fetch_asml22en():
    """ASML Holding 2022 English AFR filing."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('asml22en')


@_recorder.record(file_path=urlmock.path('asml22en_entities'))
def _fetch_asml22en_entities():
    """ASML Holding 2022 English AFR filing with entity."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
            'include': 'entity'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('asml22en_entities')


@_recorder.record(file_path=urlmock.path('asml22en_vmessages'))
def _fetch_asml22en_vmessages():
    """ASML Holding 2022 English AFR filing with validation messages."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'include': 'validation_messages',
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('asml22en_vmessages')


@_recorder.record(file_path=urlmock.path('assicurazioni21it_vmessages'))
def _fetch_assicurazioni21it_vmessages():
    """
    Assicurazioni Generali 2021 Italian AFR filing with validation
    messages.
    """
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'include': 'validation_messages',
            # fxo_id = filing_index
            'filter[fxo_id]': '549300X5UKJVE386ZB61-2021-12-31-ESEF-IT-0'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('assicurazioni21it_vmessages')


@_recorder.record(file_path=urlmock.path('tecnotree21fi_vmessages'))
def _fetch_tecnotree21fi_vmessages():
    """Tecnotree 2021 Finnish AFR filing with validation messages."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'include': 'validation_messages',
            # fxo_id = filing_index
            'filter[fxo_id]': '743700MRPVYI7ASHCX38-2021-12-31-ESEF-FI-0'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('tecnotree21fi_vmessages')


@_recorder.record(file_path=urlmock.path('asml22en_ent_vmsg'))
def _fetch_asml22en_ent_vmsg():
    """
    ASML Holding 2022 English AFR filing with entities and v-messages.
    """
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
            'include': 'entity,validation_messages'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('asml22en_ent_vmsg')


@_recorder.record(file_path=urlmock.path('filter_language'))
def _fetch_filter_language():
    """Filter by language 'fi'."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[language]': 'fi',
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_language')


@_recorder.record(file_path=urlmock.path('filter_last_end_date'))
def _fetch_filter_last_end_date():
    """Filter by last_end_date '2021-02-28'."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[period_end]': '2021-02-28', # last_end_date
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_last_end_date', lax_fixture=True)


@_recorder.record(file_path=urlmock.path('filter_error_count'))
def _fetch_filter_error_count():
    """Filter by error_count value 0."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[error_count]': 0
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_error_count')


@_recorder.record(file_path=urlmock.path('filter_inconsistency_count'))
def _fetch_filter_inconsistency_count():
    """Filter by `inconsistency_count` value 0."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[inconsistency_count]': 0
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_inconsistency_count')


@_recorder.record(file_path=urlmock.path('filter_warning_count'))
def _fetch_filter_warning_count():
    """Filter by warning_count value 0."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[warning_count]': 0
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_warning_count')


@_recorder.record(file_path=urlmock.path('filter_added_time'))
def _fetch_filter_added_time():
    """Filter by added_time value '2021-09-23 00:00:00'."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[date_added]': '2021-09-23 00:00:00' # added_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_added_time', lax_fixture=True)


@_recorder.record(file_path=urlmock.path('filter_added_time_2'))
def _fetch_filter_added_time_2():
    """Filter by added_time value '2023-05-09 13:27:02.676029'."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[date_added]': '2023-05-09 13:27:02.676029' # added_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_added_time_2')


@_recorder.record(file_path=urlmock.path('filter_entity_api_id'))
def _fetch_filter_entity_api_id():
    """Return error when filtering with `entity_api_id`."""
    kone_id = '2499'
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[entity_api_id]': kone_id
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_entity_api_id', lax_fixture=True)


@_recorder.record(file_path=urlmock.path('filter_json_url'))
def _fetch_filter_json_url():
    """Filter by json_url of Kone 2022 [en] filing."""
    json_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/2138001CNF45JP5XZK38-'
        '2022-12-31-en.json'
        )
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[json_url]': json_url
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_json_url')


@_recorder.record(file_path=urlmock.path('filter_package_url'))
def _fetch_filter_package_url():
    """Filter by package_url of Kone 2022 [en] filing."""
    package_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/'
        '2138001CNF45JP5XZK38-2022-12-31-EN.zip'
        )
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[package_url]': package_url
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_package_url')


@_recorder.record(file_path=urlmock.path('filter_viewer_url'))
def _fetch_filter_viewer_url():
    """Filter by viewer_url of Kone 2022 [en] filing."""
    viewer_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/2138001CNF45JP5XZK38-'
        '2022-12-31-EN/reports/ixbrlviewer.html'
        )
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[viewer_url]': viewer_url
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_viewer_url')


@_recorder.record(file_path=urlmock.path('filter_xhtml_url'))
def _fetch_filter_xhtml_url():
    """Filter by xhtml_url of Kone 2022 [en] filing."""
    xhtml_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/2138001CNF45JP5XZK38-'
        '2022-12-31-EN/reports/2138001CNF45JP5XZK38-2022-12-31-en.html'
        )
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[report_url]': xhtml_url
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_xhtml_url')


@_recorder.record(file_path=urlmock.path('filter_package_sha256'))
def _fetch_filter_package_sha256():
    """Filter by package_sha256 of Kone 2022 filing."""
    filter_sha = (
        'e489a512976f55792c31026457e86c9176d258431f9ed645451caff9e4ef5f80')
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[sha256]': filter_sha # package_sha256
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('filter_package_sha256')


@_recorder.record(file_path=urlmock.path('finnish_jan22'))
def _fetch_finnish_jan22():
    """Finnish AFR filings with reporting period ending in Jan 2022."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 2,
            'filter[country]': 'FI',
            'filter[period_end]': '2022-01-31' # last_end_date
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('finnish_jan22')


@_recorder.record(file_path=urlmock.path('oldest3_fi'))
def _fetch_oldest3_fi():
    """Oldest 3 AFR filings reported in Finland."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 3,
            'filter[country]': 'FI',
            'sort': 'date_added' # added_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('oldest3_fi')


@_recorder.record(file_path=urlmock.path('oldest3_fi_entities'))
def _fetch_oldest3_fi_entities():
    """Oldest 3 AFR filings reported in Finland with entities."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 3,
            'filter[country]': 'FI',
            'sort': 'date_added', # added_time
            'include': 'entity'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('oldest3_fi_entities')


@_recorder.record(file_path=urlmock.path('oldest3_fi_vmessages'))
def _fetch_oldest3_fi_vmessages():
    """
    Oldest 3 AFR filings reported in Finland with validation messages.
    """
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 3,
            'filter[country]': 'FI',
            'sort': 'date_added', # added_time
            'include': 'validation_messages'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('oldest3_fi_vmessages')


@_recorder.record(file_path=urlmock.path('oldest3_fi_ent_vmessages'))
def _fetch_oldest3_fi_ent_vmessages():
    """
    Oldest 3 AFR filings reported in Finland with entities and
    validation messages.
    """
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 3,
            'filter[country]': 'FI',
            'sort': 'date_added', # added_time
            'include': 'entity,validation_messages'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('oldest3_fi_ent_vmessages')


@_recorder.record(file_path=urlmock.path('sort_two_fields'))
def _fetch_sort_two_fields():
    """
    Sort Finnish filings by `last_end_date` and `added_time`. WARNING,
    volatile with ``mock_upgrade.py`` run. See test
    ``test_query_sort::test_sort_two_fields``.
    """
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 2,
            'filter[country]': 'FI',
            'sort': 'period_end,processed' # last_end_date, processed_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('sort_two_fields')


@_recorder.record(file_path=urlmock.path('paging_swedish_size2_pg3'))
def _fetch_paging_swedish_size2_pg3():
    """
    Get 3 pages, actually 4, (pg size 2) of oldest Swedish filings.
    """
    page_count = 4 # API bug due to not fulfilling on 3rd page
    params={
        'page[size]': 2,
        'filter[country]': 'SE',
        'sort': 'date_added' # added_time
        }
    for page_num in range(1, page_count+1):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params=params,
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
        params['page[number]'] = page_num + 1
_addmock('paging_swedish_size2_pg3', lax_fixture=True)


@_recorder.record(file_path=urlmock.path('paging_oldest_ukrainian_2pg_4ea'))
def _fetch_paging_oldest_ukrainian_2pg_4ea():
    """Get oldest Ukrainian filings 2 pages, 4 filings each."""
    page_count = 2
    params={
        'page[size]': 4,
        'filter[country]': 'UA',
        'sort': 'period_end,processed' # last_end_date, processed_time
        }
    for page_num in range(1, page_count+1):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params=params,
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
        params['page[number]'] = page_num + 1
_addmock('paging_oldest_ukrainian_2pg_4ea')


@_recorder.record(file_path=urlmock.path('multifilter_api_id'))
def _fetch_multifilter_api_id():
    """Get 4 Shell filings for 2021 and 2022."""
    for id_i, api_id in enumerate(('1134', '1135', '4496', '4529')):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 4 - id_i,
                'filter[id]': api_id
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('multifilter_api_id')


@_recorder.record(file_path=urlmock.path('multifilter_api_id_entities'))
def _fetch_multifilter_api_id_entities():
    """Get 4 Shell filings for 2021 and 2022 with entities."""
    for id_i, api_id in enumerate(('1134', '1135', '4496', '4529')):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 4 - id_i,
                'filter[id]': api_id,
                'include': 'entity'
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('multifilter_api_id_entities')


@_recorder.record(file_path=urlmock.path('multifilter_country'))
def _fetch_multifilter_country():
    """Get three filings for the country `FI`."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 3,
            'filter[country]': 'FI'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('multifilter_country')


@_recorder.record(file_path=urlmock.path('multifilter_filing_index'))
def _fetch_multifilter_filing_index():
    """Get both Shell 2021 filings filtered with filing_index."""
    fxo_codes = (
        '21380068P1DRHMJ8KU70-2021-12-31-ESEF-GB-0',
        '21380068P1DRHMJ8KU70-2021-12-31-ESEF-NL-0'
        )
    for fxo_i, fxo in enumerate(fxo_codes):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 2 - fxo_i,
                'filter[fxo_id]': fxo # filing_index
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('multifilter_filing_index')


@_recorder.record(file_path=urlmock.path('multifilter_reporting_date'))
def _fetch_multifilter_reporting_date():
    """Return an error for filtering with `reporting_date`."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 3,
            'filter[reporting_date]': '2020-12-31'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('multifilter_reporting_date')


@_recorder.record(file_path=urlmock.path('multifilter_processed_time'))
def _fetch_multifilter_processed_time():
    """Get two filings filtered with `processed_time`."""
    cloetta_sv_strs = (
        '2023-01-18 11:02:06.724768',
        '2023-05-16 21:07:17.825836'
        )
    for filter_i, filter_str in enumerate(cloetta_sv_strs):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 2 - filter_i,
                'filter[processed]': filter_str # processed_time
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('multifilter_processed_time')


@_recorder.record(file_path=urlmock.path('unknown_filter_error'))
def _fetch_unknown_filter_error():
    """Get an error of unknown filter."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[abcdef]': '0'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('unknown_filter_error')


@_recorder.record(file_path=urlmock.path('bad_page_error'))
def _fetch_bad_page_error():
    """Get an error of page number -1."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 30,
            'page[number]': -1
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('bad_page_error')


@_recorder.record(file_path=urlmock.path('fortum23fi_xhtml_language'))
def _fetch_fortum23fi_xhtml_language():
    """Fortum 2023 Finnish AFR filing with language in xhtml_url."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 1,
            'filter[id]': '12366', # api_id
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('fortum23fi_xhtml_language')


@_recorder.record(file_path=urlmock.path('paging_czechia20dec'))
def _fetch_paging_czechia20dec():
    """Czech 2020-12-31 AFRs."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 10,
            'filter[country]': 'CZ',
            'filter[period_end]': '2020-12-31', # last_end_date
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 10,
            'filter[country]': 'CZ',
            'filter[period_end]': '2020-12-31',
            'page[number]': 2
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 10,
            'filter[country]': 'CZ',
            'filter[period_end]': '2020-12-31',
            'page[number]': 3
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('paging_czechia20dec')


@_recorder.record(file_path=urlmock.path('multifilter_belgium20_short_date_year'))
def _fetch_multifilter_belgium20_short_date_year():
    """
    Belgian 2020 AFRs querying with short date filter year,
    limit=100.
    """
    date_list = (
        '2020-08-31',
        '2020-09-30',
        '2020-10-31',
        '2020-11-30',
        '2020-12-31', # 21 filings
        '2021-01-31',
        '2021-02-28',
        '2021-03-31', # 10 filings
        '2021-04-30',
        '2021-05-31',
        '2021-06-30',
        '2021-07-31',
        )
    filings_left = 100 # min(options.max_page_size, limit)
    for date_str in date_list:
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': filings_left,
                'filter[country]': 'BE',
                'filter[period_end]': date_str, # last_end_date
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
        if date_str == '2020-12-31':
            filings_left -= 21
        elif date_str == '2021-03-31':
            filings_left -= 10
_addmock('multifilter_belgium20_short_date_year')


@_recorder.record(file_path=urlmock.path('multifilter_belgium20_short_date_year_no_limit'))
def _fetch_multifilter_belgium20_short_date_year_no_limit():
    """
    Belgian 2020 AFRs querying with short date filter year,
    limit=NO_LIMIT, options.max_page_size=200.
    """
    date_list = (
        '2020-08-31',
        '2020-09-30',
        '2020-10-31',
        '2020-11-30',
        '2020-12-31', # 21 filings
        '2021-01-31',
        '2021-02-28',
        '2021-03-31', # 10 filings
        '2021-04-30',
        '2021-05-31',
        '2021-06-30',
        '2021-07-31',
        )
    filings_left = 200 # min(options.max_page_size, limit)
    for date_str in date_list:
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': filings_left,
                'filter[country]': 'BE',
                'filter[period_end]': date_str, # last_end_date
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('multifilter_belgium20_short_date_year_no_limit')


@_recorder.record(file_path=urlmock.path('sort_asc_package_sha256_latvia'))
def _fetch_sort_asc_package_sha256_latvia():
    """Sorted ascending by package_sha256 from Latvian records."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 4,
            'filter[country]': 'LV',
            'sort': 'sha256', # package_sha256
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('sort_asc_package_sha256_latvia')


@_recorder.record(file_path=urlmock.path('sort_desc_package_sha256_latvia'))
def _fetch_sort_desc_package_sha256_latvia():
    """Sorted ascending by package_sha256 from Latvian records."""
    _ = requests.get(
        url=ENTRY_POINT_URL,
        params={
            'page[size]': 4,
            'filter[country]': 'LV',
            'sort': '-sha256', # package_sha256
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
_addmock('sort_desc_package_sha256_latvia')


@_recorder.record(file_path=urlmock.path('kone22_all_languages'))
def _fetch_kone22_all_languages():
    """Sorted ascending by package_sha256 from Latvian records."""
    kone22_api_ids = ['4143', '4144']
    for req_i, api_id in enumerate(kone22_api_ids):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 100 - req_i,
                'filter[id]': api_id,
                'include': 'entity'
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('kone22_all_languages')


@_recorder.record(file_path=urlmock.path('estonian_2_pages_3_each'))
def _fetch_estonian_2_pages_3_each():
    """
    Estonian filings 2 pages of size 3, incl. entities, v-messages.
    """
    page_count = 2
    params={
        'page[size]': 3,
        'filter[country]': 'EE',
        'include': 'entity,validation_messages'
        }
    for page_num in range(1, page_count+1):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params=params,
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
        params['page[number]'] = page_num + 1
_addmock('estonian_2_pages_3_each')


@_recorder.record(file_path=urlmock.path('ageas21_22'))
def _fetch_ageas21_22():
    """
    Ageas 2021 and 2022 filings in 3 languages (nl, fr, en) with
    entities, 6 filings.
    """
    ageas21_22_ids = '3314', '3316', '3315', '5139', '5140', '5141'
    for req_i, api_id in enumerate(ageas21_22_ids):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 6 - req_i,
                'filter[id]': api_id,
                'include': 'entity'
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('ageas21_22')


@_recorder.record(file_path=urlmock.path('applus20_21'))
def _fetch_applus20_21():
    """
    Applus Services 2020, 2021 filings with entities, 2 filings, same
    last_end_date.
    """
    applus20_21_ids = '1733', '1734'
    for req_i, api_id in enumerate(applus20_21_ids):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 2 - req_i,
                'filter[id]': api_id,
                'include': 'entity'
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('applus20_21')


@_recorder.record(file_path=urlmock.path('upm21to22'))
def _fetch_upm21to22():
    """
    UPM-Kymmene 2021 to 2022 filings (en, fi) with entities, 4 filings.
    """
    # Order: 21en, 21fi, 22en, 22fi
    upm21to22_ids = ['138', '137', '4455', '4456']
    for req_i, api_id in enumerate(upm21to22_ids):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 4 - req_i,
                'filter[id]': api_id,
                'include': 'entity,validation_messages'
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('upm21to22')


@_recorder.record(file_path=urlmock.path('upm22to23'))
def _fetch_upm22to23():
    """
    UPM-Kymmene 2022 to 2023 filings (en, fi) with entities, 4 filings.
    """
    # Order: 22en, 22fi, 23en, 23fi
    upm22to23_ids = ['4455', '4456', '12499', '12500']
    for req_i, api_id in enumerate(upm22to23_ids):
        _ = requests.get(
            url=ENTRY_POINT_URL,
            params={
                'page[size]': 4 - req_i,
                'filter[id]': api_id,
                'include': 'entity,validation_messages'
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )
_addmock('upm22to23')

################ END OF MOCK URL COLLECTION DEFINITIONS ################


def main():
    """Run the command line interface."""
    parser = argparse.ArgumentParser(
        description=(
            'Script for updating mock URL collections for tests in '
            f'folder "{MOCK_URL_DIR_NAME}".'
            ),
        epilog=(
            'Mocks removed from the listing in this script will be '
            'removed from the mock folder as well.'
            )
        )

    parser.add_argument(
        '-a', '--all', action='store_true',
        help='upgrade all mock URL collections'
        )
    parser.add_argument(
        '-n', '--new', action='store_true',
        help='upgrade only new, unfetched mock URL collections'
        )
    parser.add_argument(
        '-l', '--list', action='store_true',
        help='list all mocks defined in this module'
        )
    parser.add_argument(
        '-b', '--bare-list', action='store_true',
        help='use simple bare list format with --list'
        )

    clargs = parser.parse_args()

    if clargs.all:
        _upgrade_mock_urls(only_new=False)
    elif clargs.new:
        _upgrade_mock_urls(only_new=True)
    elif clargs.list:
        _list_mock_urls(clargs.bare_list)
    else:
        parser.print_help()


def _upgrade_mock_urls(only_new):
    # Ensure directory exists
    mock_dir_path.mkdir(parents=True, exist_ok=True)

    fetch_count = len(urlmock_defs)
    if only_new:
        fetch_count = _flag_new_for_fetching()
        print(
            f'\nUpgrading {fetch_count} unfetched mock URL '
            'collection(s)\n'
            )
    else:
        print(
            f'\nUpgrading all {fetch_count} mock URL collections\n')

    # Run recorder functions
    with open(conftest_out_spath, 'w', encoding='utf-8') as ctout:

        # Write non-generated conftest.py contents
        with open(conftest_src_spath, 'r', encoding='utf-8') as ctsource:
            skip_until_newline = False
            for line in ctsource:
                if skip_until_newline:
                    skip_until_newline = line != '\n'
                elif line.startswith('EDITABLE: '):
                    ctout.write(NO_EDIT_DOCSTRING.lstrip() + '\n')
                    skip_until_newline = True
                else:
                    wline = line
                    for noqa_line in remove_unnecessary_import_noqa_lines:
                        if line == noqa_line:
                            # Remove noqa part
                            wline = wline[:-15] + '\n'
                    ctout.write(wline)

        # Iterate URL mock collections, download and save request
        # contents and append conftext.py accordingly
        for mock in urlmock_defs.values():
            py_code = _mock_url_to_py_code(mock)
            ctout.write('\n' + py_code)

            if not mock.isfetch:
                continue
            print(f'> {mock.name}')
            mock.fetch()

    _delete_files_of_removed_mocks()

    if only_new:
        print(f'\nFetched {fetch_count} new mock(s)')
    else:
        print('\nFetched all mocks')
    print(f'\nUpdated "{CONFTEST_OUT_PATH}"')
    print(f'\nFolder path: {mock_dir_path}')


def _mock_url_to_py_code(mock):
    """Write generated conftest.py contents for URL mock collections."""
    gen_py_list = []
    for islax in range(2 if mock.lax_fixture else 1):
        fixt_name = mock.name
        param_str = ''
        if islax:
            fixt_name = f'{fixt_name}_lax'
            param_str = URL_MOCK_PARAM_LAX

        fmt_doc = mock.fetch.__doc__.strip()
        fmt_doc = re.sub(r'(?!<\n)\n +(?!\n)', ' ', fmt_doc)
        if len(fmt_doc) > 62: # 72 - 6 - 4 (docstring quotes and tab)
            fmt_doc = textwrap.fill(
                text=fmt_doc,
                width=72,
                initial_indent=' '*4,
                subsequent_indent=' '*4,
                expand_tabs=False,
                replace_whitespace=True,
                break_long_words=True,
                break_on_hyphens=True,
                drop_whitespace=True,
                )
            fmt_doc = f'\n{fmt_doc}\n' + ' '*4
        gen_py_list.append(
            URL_MOCK_FIXTURE_TEMPLATE.format(
                name=mock.name,
                fixt_name=fixt_name,
                docstring=fmt_doc,
                param_str=param_str
                ))
    return '\n'.join(gen_py_list)


def _list_mock_urls(bare_list):
    new_count = _flag_new_for_fetching()
    new_text = f' ({new_count} new)' if new_count else ''
    if not bare_list:
        print(f'\nFound {len(urlmock_defs)} mock URL collections{new_text}:')
    for mock in urlmock_defs.values():
        if bare_list:
            print(mock.name)
        else:
            print('\n' + mock.name, end='')
            par_parts = []
            if mock.lax_fixture:
                par_parts.append('lax available')
            if mock.isfetch:
                par_parts.append('unfetched')
            if par_parts:
                print(' (' + ', '.join(par_parts) + ')')
            else:
                print()
            fmt_doc = re.sub(r'\s{2,}', ' ', mock.fetch.__doc__.strip())
            fmt_doc = textwrap.fill(
                text=fmt_doc,
                width=72,
                initial_indent=' '*4,
                subsequent_indent=' '*4,
                expand_tabs=False,
                replace_whitespace=True,
                break_long_words=True,
                break_on_hyphens=True,
                drop_whitespace=True,
                )
            print(fmt_doc)


def _delete_files_of_removed_mocks():
    mock_names = set(urlmock_defs.keys())
    deleted_files = []
    for filepath in mock_dir_path.iterdir():
        if filepath.stem not in mock_names:
            filepath.unlink()
            deleted_files.append(filepath.name)
    if deleted_files:
        print('\nDeleted files of removed mocks in following files:\n')
        for filename in deleted_files:
            print(f'{MOCK_URL_DIR_NAME}/{filename}')


def _flag_new_for_fetching():
    existing_count = 0
    for mock in urlmock_defs.values():
        mock_path = mock_dir_path / f'{mock.name}.yaml'
        if mock_path.is_file():
            mock.isfetch = False
            existing_count += 1
    return len(urlmock_defs) - existing_count


if __name__ == '__main__':
    main()
