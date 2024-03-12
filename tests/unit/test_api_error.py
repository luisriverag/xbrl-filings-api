"""Define tests for `APIError`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api as xf
import xbrl_filings_api.exceptions as xf_exceptions


@pytest.fixture
def unknown_filter_error_obj(unknown_filter_error_response):
    with pytest.warns(xf_exceptions.FilterNotSupportedWarning):
        with pytest.raises(xf.APIError) as exc_info:
            _ = xf.get_filings(
                filters={'abcdef': '0'},
                sort=None,
                max_size=1,
                flags=xf.GET_ONLY_FILINGS,
                add_api_params=None
                )
    return exc_info.value


@pytest.fixture
def bad_page_error_obj(bad_page_error_response):
    with pytest.raises(xf.APIError) as exc_info:
        _ = xf.get_filings(
            filters=None,
            sort=None,
            max_size=30,
            flags=xf.GET_ONLY_FILINGS,
            add_api_params={'page[number]': -1}
            )
    return exc_info.value


def test_unknown_filter(unknown_filter_error_obj):
    err: xf.APIError = unknown_filter_error_obj
    assert err.title == 'Invalid filters querystring parameter.'
    assert err.detail == 'FilingSchema has no attribute abcdef'
    assert err.code is None
    assert err.api_status == '400'
    assert err.status == 400
    assert err.status_text == 'Bad Request'


def test_bad_page(bad_page_error_obj):
    err: xf.APIError = bad_page_error_obj
    assert err.title == 'Unknown error'
    assert err.detail is None
    assert err.code == '9h9h'
    assert err.api_status == '500'
    assert err.status == 500
    assert err.status_text == 'Internal Server Error'


def test_str_unknown_filter(unknown_filter_error_obj):
    """Test `__str__` for mock unknown_filter_error."""
    e_str = (
        'Invalid filters querystring parameter. | '
        'FilingSchema has no attribute abcdef'
        )
    err: xf.APIError = unknown_filter_error_obj
    assert str(err) == e_str


def test_repr_unknown_filter(unknown_filter_error_obj):
    """Test `__repr__` for mock unknown_filter_error."""
    e_repr = (
        "APIError(title='Invalid filters querystring parameter.', "
        "detail='FilingSchema has no attribute abcdef', code=None)"
        )
    err: xf.APIError = unknown_filter_error_obj
    assert repr(err) == e_repr


def test_str_bad_page(bad_page_error_obj):
    """Test `__str__` for mock bad_page_error."""
    e_str = 'Unknown error (9h9h)'
    err: xf.APIError = bad_page_error_obj
    assert str(err) == e_str


def test_repr_bad_page(bad_page_error_obj):
    """Test `__repr__` for mock bad_page_error."""
    e_repr = "APIError(title='Unknown error', detail=None, code='9h9h')"
    err: xf.APIError = bad_page_error_obj
    assert repr(err) == e_repr
