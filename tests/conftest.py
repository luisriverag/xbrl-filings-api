"""
Configuration of `pytest` library.

.. note::
    This script uses beta feature `responses._add_from_file` (as of
    `responses` version 0.23.3).
"""

from pathlib import Path

import pytest
import responses

MOCK_URL_DIR_NAME = '.mock_url_cache'

mock_dir_path = Path(__file__).parent / MOCK_URL_DIR_NAME


def _get_absolute_path(set_id):
    file_path = mock_dir_path / f'{set_id}_mock.yaml'
    return str(file_path)


@pytest.fixture
def api_responses():
    """Fixture for mocked 'api' responses."""
    with responses.RequestsMock() as rsps:
        rsps._add_from_file(_get_absolute_path('api'))
        yield rsps
