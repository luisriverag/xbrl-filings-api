"""Define tests for query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import responses

from xbrl_filings_api import GET_ONLY_FILINGS, query


class Test_get_filings:
    def test_fetch_asml22(api_responses):
        fs = query.get_filings(
            filters={'entity.identifier': '724500Y6DUVHQD6OXN27'},
            max_size=2,
            flags=GET_ONLY_FILINGS
            )
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        asml22 = next((f for f in fs if f.filing_index == asml22_fxo), None)
        assert asml22 is not None, 'Requested filing was not returned'

    def test_fetch_asml22_country(api_responses):
        fs = query.get_filings(
            filters={'entity.identifier': '724500Y6DUVHQD6OXN27'},
            max_size=2,
            flags=GET_ONLY_FILINGS
            )
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        asml22 = next((f for f in fs if f.filing_index == asml22_fxo), None)
        assert asml22.country == 'NL'

# query.to_sqlite
# query.filing_page_iter
