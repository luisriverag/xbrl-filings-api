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

from pathlib import Path
from types import FunctionType

import requests
from responses import _recorder

# Define mock URLs to be downloaded
MOCK_URL_SET_IDS = (
    'creditsuisse21en_by_id',
    'asml22en',
    'asml22en_entities',
    'asml22en_vmessages',
    'asml22en_ent_vmsg',
    'filter_language',
    'filter_last_end_date',
    'filter_error_count',
    'filter_added_time',
    'filter_package_url',
    'filter_package_sha256',
    'finnish_jan22',
    'oldest3_fi',
    'sort_two_fields',
    'multipage',
    'api_id_multifilter',
    # 'download',
    )

MOCK_URL_DIR_NAME = 'mock_responses'
entry_point_url = 'https://filings.xbrl.org/api/filings'

mock_dir_path = Path(__file__).parent / MOCK_URL_DIR_NAME
JSON_API_HEADERS = {
    'Content-Type': 'application/vnd.api+json'
    }
REQUEST_TIMEOUT = 30.0


def _get_absolute_path(set_id):
    file_path = mock_dir_path / f'{set_id}.yaml'
    return str(file_path)


set_paths = {set_id: _get_absolute_path(set_id) for set_id in MOCK_URL_SET_IDS}


def _ensure_dir_exists():
    some_path = next(iter(set_paths.values()))
    Path(some_path).parent.mkdir(parents=True, exist_ok=True)


@_recorder.record(file_path=set_paths['creditsuisse21en_by_id'])
def _fetch_creditsuisse21en_by_id():
    """Credit Suisse 2021 English AFR filing by `api_id`."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            # id = api_id
            'filter[id]': '162',
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['asml22en'])
def _fetch_asml22en():
    """ASML Holding 2022 English AFR filing."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['asml22en_entities'])
def _fetch_asml22en_entities():
    """ASML Holding 2022 English AFR filing with entity."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
            'include': 'entity'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['asml22en_vmessages'])
def _fetch_asml22en_vmessages():
    """ASML Holding 2022 English AFR filing with validation messages."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            'include': 'validation_messages',
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['asml22en_ent_vmsg'])
def _fetch_asml22en_ent_vmsg():
    """ASML Holding 2022 English AFR filing with entities and v-messages."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            # fxo_id = filing_index
            'filter[fxo_id]': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
            'include': 'entity,validation_messages'
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['filter_language'])
def _fetch_filter_language():
    """Filter by language 'fi'."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            'filter[language]': 'fi',
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['filter_last_end_date'])
def _fetch_filter_last_end_date():
    """Filter by last_end_date '2021-02-28'."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            'filter[period_end]': '2021-02-28', # last_end_date
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['filter_error_count'])
def _fetch_filter_error_count():
    """Filter by error_count value 1."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            'filter[error_count]': 1
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['filter_added_time'])
def _fetch_filter_added_time():
    """Filter by added_time value '2021-09-23 00:00:00'."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            'filter[date_added]': '2021-09-23 00:00:00' # added_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['filter_package_url'])
def _fetch_filter_package_url():
    """Filter by package_url of Kone 2022 filing."""
    filter_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/'
        '2138001CNF45JP5XZK38-2022-12-31-EN.zip'
        )
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            'filter[package_url]': filter_url
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['filter_package_sha256'])
def _fetch_filter_package_sha256():
    """Filter by package_sha256 of Kone 2022 filing."""
    filter_sha = (
        'e489a512976f55792c31026457e86c9176d258431f9ed645451caff9e4ef5f80')
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 1,
            'filter[sha256]': filter_sha # package_sha256
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['finnish_jan22'])
def _fetch_finnish_jan22():
    """Finnish AFR filings with reporting period ending in Jan 2022."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 2,
            'filter[country]': 'FI',
            'filter[period_end]': '2022-01-31' # last_end_date
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['oldest3_fi'])
def _fetch_oldest3_fi():
    """Oldest 3 AFR filings reported in Finland."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 3,
            'filter[country]': 'FI',
            'sort': 'date_added' # added_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['sort_two_fields'])
def _fetch_sort_two_fields():
    """
    Sort Finnish filings by `last_end_date` and `added_time`.

    .. warning::

        Volatile with ``mock_upgrade.py`` run. See test
        ``test_query::Test_get_filings::test_sort_two_fields``.
    """
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 2,
            'filter[country]': 'FI',
            'sort': 'period_end,processed' # last_end_date, processed_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['multipage'])
def _fetch_multipage():
    """Get 3 pages (2pc) of oldest Swedish filings."""
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 2,
            'filter[country]': 'SE',
            'sort': 'date_added' # added_time
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 2,
            'filter[country]': 'SE',
            'sort': 'date_added', # added_time
            'page[number]': 2
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 2,
            'filter[country]': 'SE',
            'sort': 'date_added', # added_time
            'page[number]': 3
            },
        headers=JSON_API_HEADERS,
        timeout=REQUEST_TIMEOUT
        )


@_recorder.record(file_path=set_paths['api_id_multifilter'])
def _fetch_api_id_multifilter():
    """Get 4 Shell filings for 2021 and 2022."""
    for api_id in ('1134', '1135', '4496', '4529'):
        _ = requests.get(
            url=entry_point_url,
            params={
                'page[size]': 4,
                'filter[id]': api_id
                },
            headers=JSON_API_HEADERS,
            timeout=REQUEST_TIMEOUT
            )


# @_recorder.record(file_path=set_paths['download'])
# def _fetch_download():
#     """Record mock URLs to file."""
#     _ = requests.get(
#         url="",
#         stream=True,
#         timeout=REQUEST_TIMEOUT
#         )


def _delete_removed_mocks():
    some_path = next(iter(set_paths.values()))
    for filepath in Path(some_path).parent.iterdir():
        if filepath.stem not in MOCK_URL_SET_IDS:
            filepath.unlink()
            print(f'Deleted removed mock in file "{filepath.name}"')


if __name__ == '__main__':
    _ensure_dir_exists()

    # Run recorder functions
    gitems = globals().copy()
    for name, val in gitems.items():
        if name.startswith('_fetch_') and isinstance(val, FunctionType):
            val()

    _delete_removed_mocks()

    print(
        'Mock upgrade finished\n'
        f'Folder path: {mock_dir_path}'
        f'\n  - ' + '\n  - '.join(MOCK_URL_SET_IDS)
        )
else:
    msg = 'This module must be run as a script.'
    raise NotImplementedError(msg)
