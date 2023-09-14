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

from pathlib import Path

import requests
from responses import _recorder

MOCK_URL_SET_IDS = (
    'api',
    'download',
    )
MOCK_URL_DIR_NAME = '.mock_url_cache'
entry_point_url = 'https://filings.xbrl.org/api/filings'

mock_dir_path = Path(__file__).parent / MOCK_URL_DIR_NAME


def _get_absolute_path(set_id):
    file_path = mock_dir_path / f'{set_id}_mock.yaml'
    return str(file_path)


set_paths = {set_id: _get_absolute_path(set_id) for set_id in MOCK_URL_SET_IDS}


def _ensure_dir_exists():
    some_path = next(iter(set_paths.values()))
    Path(some_path).parent.mkdir(parents=True, exist_ok=True)


@_recorder.record(file_path=set_paths['api'])
def _get_api_mocks():
    """Record mock URLs to file."""
    jsonapi_headers = {
        'Content-Type': 'application/vnd.api+json'
        }
    _ = requests.get(
        url=entry_point_url,
        params={
            'page[size]': 2,
            'filter[entity.identifier]': '724500Y6DUVHQD6OXN27',
            },
        headers=jsonapi_headers,
        timeout=30
        )


@_recorder.record(file_path=set_paths['download'])
def _get_download_mocks():
    """Record mock URLs to file."""
    # _ = requests.get(
    #     url="",
    #     stream=True,
    #     timeout=30
    #     )


if __name__ == '__main__':
    _ensure_dir_exists()
    _get_api_mocks()
    _get_download_mocks()
else:
    msg = 'This module must be run as a script.'
    raise NotImplementedError(msg)
