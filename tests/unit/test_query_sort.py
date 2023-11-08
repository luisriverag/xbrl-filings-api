"""Define tests for sorting in query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import sqlite3
from datetime import datetime, timezone

import pytest

import xbrl_filings_api as xf

UTC = timezone.utc


def _db_record_count(cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0]


def test_sort_oldest_finnish_str(oldest3_fi_response, monkeypatch):
    """Sort by `added_time` for filings from Finland."""
    fs = xf.get_filings(
        filters={
            'country': 'FI'
            },
        sort='added_time',
        max_size=3,
        flags=xf.GET_ONLY_FILINGS
        )
    date_max = datetime(2021, 5, 18, 0, 0, 1, tzinfo=UTC)
    for f in fs:
        assert f.added_time < date_max, 'Before 2021-05-18T00:00:01Z'


def test_sort_oldest_finnish_list(oldest3_fi_response, monkeypatch):
    """Sort by `added_time` for filings from Finland."""
    fs = xf.get_filings(
        filters={
            'country': 'FI'
            },
        sort=['added_time'],
        max_size=3,
        flags=xf.GET_ONLY_FILINGS
        )
    date_max = datetime(2021, 5, 18, 0, 0, 1, tzinfo=UTC)
    for f in fs:
        assert f.added_time < date_max, 'Before 2021-05-18T00:00:01Z'


def test_sort_two_fields(sort_two_fields_response):
    """
    Sort by `last_end_date`, `processed_time` for Finland filings.

    .. warning::

        This test is volatile regarding `mock_upgrade.py` runs.
        Systematically ancient (erraneous?) fact dates in new issued
        filings or introduction of older reports using other
        accounting principles/XBRL taxonomies may break it.
    """
    fs = xf.get_filings(
        filters={
            'country': 'FI'
            },
        sort=['last_end_date', 'processed_time'],
        max_size=2,
        flags=xf.GET_ONLY_FILINGS
        )
    assert len(fs) == 2, 'Two filings were requested'
    filing_indexes = {f.filing_index for f in fs}
    # TODO: Must be checked from full database output
    neste20en_fxo = '5493009GY1X8GQ66AM14-2020-12-31-ESEF-FI-0'
    assert neste20en_fxo in filing_indexes
    neste20fi_fxo = '5493009GY1X8GQ66AM14-2020-12-31-ESEF-FI-1'
    assert neste20fi_fxo in filing_indexes


# to_sqlite
# filing_page_iter
