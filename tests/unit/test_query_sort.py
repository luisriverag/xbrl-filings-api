"""Define tests for sorting in query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

from datetime import datetime, timezone

import pytest

import xbrl_filings_api as xf

UTC = timezone.utc


@pytest.mark.datetime
def test_sort_oldest_finnish_str(oldest3_fi_response, monkeypatch):
    """Sort by string `added_time` for filings from Finland."""
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


@pytest.mark.datetime
def test_sort_oldest_finnish_list(oldest3_fi_response, monkeypatch):
    """Sort by list of string `added_time` for filings from Finland."""
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


def test_sort_asc_package_sha256(sort_asc_package_sha256_latvia_response):
    """Sort ascending by `package_sha256` for filings from Latvia."""
    pageiter = xf.filing_page_iter(
        filters={
            'country': 'LV'
            },
        sort='package_sha256',
        max_size=4,
        flags=xf.GET_ONLY_FILINGS
        )
    fpage: xf.FilingsPage = next(iter(pageiter))
    filing_list = fpage.filing_list
    assert filing_list[0].package_sha256 <= filing_list[1].package_sha256
    assert filing_list[1].package_sha256 <= filing_list[2].package_sha256
    assert filing_list[2].package_sha256 <= fpage.filing_list[3].package_sha256


def test_sort_desc_package_sha256(sort_desc_package_sha256_latvia_response):
    """Sort descending by `package_sha256` for filings from Latvia."""
    pageiter = xf.filing_page_iter(
        filters={
            'country': 'LV'
            },
        sort='-package_sha256',
        max_size=4,
        flags=xf.GET_ONLY_FILINGS
        )
    fpage: xf.FilingsPage = next(iter(pageiter))
    filing_list = fpage.filing_list
    assert filing_list[0].package_sha256 >= filing_list[1].package_sha256
    assert filing_list[1].package_sha256 >= filing_list[2].package_sha256
    assert filing_list[2].package_sha256 >= filing_list[3].package_sha256
