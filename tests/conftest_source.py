"""
Configuration of `pytest` library.

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

import pytest  # noqa: F401
import responses  # noqa: F401

MOCK_URL_DIR_NAME = 'mock_responses'

mock_dir_path = Path(__file__).parent / MOCK_URL_DIR_NAME


def _get_path(set_id):
    """Get absolute file path of the mock URL collection file."""
    file_path = mock_dir_path / f'{set_id}.yaml'
    return str(file_path)
