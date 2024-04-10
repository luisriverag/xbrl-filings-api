"""
Define tests for unsupported filters of query functions.

These tests may be moved to module `test_query_filters_single` whether
they ever are fixed in the underlying API.

Resource attributes (of filings) ending ``_count`` and ``_url`` are
currently unsupported.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api as xf


@pytest.mark.xfail(
    reason=(
        'Filtering by "_count" attributes is not supported by the '
        'API.'
        ),
    raises=xf.APIError)
def test_get_filings_error_count(filter_error_count_response):
    """Filtering by `error_count` value 1 return one filing."""
    fs = xf.get_filings(
        filters={
            'error_count': 0
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    filing = next(iter(fs), None)
    assert isinstance(filing, xf.Filing)
    assert filing.error_count == 0


@pytest.mark.xfail(
    reason=(
        'Filtering by "_count" attributes is not supported by the '
        'API.'
        ),
    raises=xf.APIError)
def test_get_filings_inconsistency_count(filter_inconsistency_count_response):
    """Requested `inconsistency_count` filings are returned."""
    fs = xf.get_filings(
        filters={
            'inconsistency_count': 0
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    filing = next(iter(fs), None)
    assert isinstance(filing, xf.Filing)
    assert filing.inconsistency_count == 0


@pytest.mark.xfail(
    reason=(
        'Filtering by "_count" attributes is not supported by the '
        'API.'
        ),
    raises=xf.APIError)
def test_get_filings_warning_count(filter_warning_count_response):
    """Requested `warning_count` filings are returned."""
    fs = xf.get_filings(
        filters={
            'warning_count': 0
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    filing = next(iter(fs), None)
    assert isinstance(filing, xf.Filing)
    assert filing.warning_count == 0


@pytest.mark.xfail(
    reason=(
        'Filtering by "_url" attributes is not supported by the '
        'API.'
        ),
    raises=xf.APIError)
def test_get_filings_json_url(filter_json_url_response):
    """Filtering by `json_url` return one filing."""
    json_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/2138001CNF45JP5XZK38-'
        '2022-12-31-en.json'
        )
    fs = xf.get_filings(
        filters={
            'json_url': json_url
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    kone22en = next(iter(fs), None)
    assert isinstance(kone22en, xf.Filing)
    assert kone22en.json_url.endswith(json_url)


@pytest.mark.xfail(
    reason=(
        'Filtering by "_url" attributes is not supported by the '
        'API.'
        ),
    raises=xf.APIError)
def test_get_filings_package_url(filter_package_url_response):
    """Filtering by `package_url` return one filing."""
    package_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/'
        '2138001CNF45JP5XZK38-2022-12-31-EN.zip'
        )
    fs = xf.get_filings(
        filters={
            'package_url': package_url
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    kone22en = next(iter(fs), None)
    assert isinstance(kone22en, xf.Filing)
    assert kone22en.package_url.endswith(package_url)


@pytest.mark.xfail(
    reason=(
        'Filtering by "_url" attributes is not supported by the '
        'API.'
        ),
    raises=xf.APIError)
def test_get_filings_viewer_url(filter_viewer_url_response):
    """Filtering by `viewer_url` return one filing."""
    viewer_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/2138001CNF45JP5XZK38-'
        '2022-12-31-EN/reports/ixbrlviewer.html'
        )
    fs = xf.get_filings(
        filters={
            'viewer_url': viewer_url
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    kone22en = next(iter(fs), None)
    assert isinstance(kone22en, xf.Filing)
    assert kone22en.viewer_url.endswith(viewer_url)


@pytest.mark.xfail(
    reason=(
        'Filtering by "_url" attributes is not supported by the '
        'API.'
        ),
    raises=xf.APIError)
def test_get_filings_xhtml_url(filter_xhtml_url_response):
    """Filtering by `xhtml_url` return one filing."""
    xhtml_url = (
        '/2138001CNF45JP5XZK38/2022-12-31/ESEF/FI/0/2138001CNF45JP5XZK38-'
        '2022-12-31-EN/reports/2138001CNF45JP5XZK38-2022-12-31-en.html'
        )
    fs = xf.get_filings(
        filters={
            'xhtml_url': xhtml_url
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    kone22en = next(iter(fs), None)
    assert isinstance(kone22en, xf.Filing)
    assert kone22en.xhtml_url.endswith(xhtml_url)
