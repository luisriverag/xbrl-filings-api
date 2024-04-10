"""Define tests for bugs in the underlying API."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api as xf


@pytest.mark.paging
@pytest.mark.xfail(
    reason=(
        'Error in the underlying API: redundant filings on pages. '
        'Filing with api_id "1" (Cloetta AB, 2021, en) and "2" '
        '(Cloetta AB, 2021, sv) are returned twice and as a result, '
        'a fouth page is requested to fulfil expected 5 filings.'
        )
    )
def test_paging_sort_added_time(
        paging_swedish_size2_pg3_lax_response, monkeypatch):
    """Requested filings are available on 3 pages."""
    monkeypatch.setattr(xf.options, 'max_page_size', 2)
    piter = xf.filing_page_iter(
        filters={
            'country': 'SE'
            },
        sort='added_time',
        limit=5,
        flags=xf.GET_ONLY_FILINGS
        )
    page1 = next(piter, None)
    assert isinstance(page1, xf.FilingsPage)
    assert len(page1.filing_list) == 2, 'Get 2 unique filings'
    page2 = next(piter, None)
    assert isinstance(page2, xf.FilingsPage)
    assert len(page2.filing_list) == 2, 'Get 2 prev unique filings, not 1'
    page3 = next(piter, None)
    assert isinstance(page3, xf.FilingsPage)
    assert len(page3.filing_list) == 2, 'Get 2 prev unique filings, not 1'
    page_none = next(piter, None)
    assert page_none is None, 'Forth page is not requested'
