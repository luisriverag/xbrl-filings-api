"""
Configuration of `pytest` library.

.. note::
    This script uses beta feature `responses._add_from_file` (as of
    `responses` version 0.23.3).
"""

import pytest
import responses


@pytest.fixture
def api_responses():
    """Fixture for mocked 'api' responses."""
    with responses.RequestsMock() as rsps:
        yield rsps
