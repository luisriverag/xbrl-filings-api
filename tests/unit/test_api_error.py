"""Define tests for `APIError`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api as xf
import xbrl_filings_api.exceptions as xf_exceptions


def test_unknown_filter(unknown_filter_error_response):
    with pytest.warns(xf_exceptions.FilterNotSupportedWarning):
        with pytest.raises(xf.APIError) as exc_info:
            _ = xf.get_filings(
                filters={'abcdef': '0'},
                sort=None,
                max_size=1,
                flags=xf.GET_ONLY_FILINGS,
                add_api_params=None
                )
    err: xf.APIError = exc_info.value
    assert err.title == 'Invalid filters querystring parameter.'
    assert err.detail == 'FilingSchema has no attribute abcdef'
    assert err.code is None
    assert err.api_status == '400'
    assert err.status == 400
    assert err.status_text == 'Bad Request'
    assert str(err) == (
        "APIError(title='Invalid filters querystring parameter.', "
        "detail='FilingSchema has no attribute abcdef', code=None)"
        )
