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

from pathlib import Path

import pytest
import responses  # noqa: F401

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
