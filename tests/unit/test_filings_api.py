"""Define tests for root functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import responses

from xbrl_filings_api import GET_ONLY_FILINGS, filings_api

MOCK_URL_DIR_NAME = '.mock_url_cache'

mock_dir_path = Path(__file__).parent.parent / MOCK_URL_DIR_NAME


def _get_absolute_path(set_id):
    file_path = mock_dir_path / f'{set_id}_mock.yaml'
    return str(file_path)


class Test_get_filings:
    @responses.activate
    def test_fetch_asml22_country(s, api_responses):
        api_responses._add_from_file(file_path=_get_absolute_path('api'))
        # ASML Holding
        fs = filings_api.get_filings(
            filters={'entity.identifier': '724500Y6DUVHQD6OXN27'},
            max_size=2,
            flags=GET_ONLY_FILINGS
            )
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        asml22 = next((f for f in fs if f.filing_index == asml22_fxo), None)
        assert asml22 is not None, 'Requested filing was not returned'
        assert asml22.country == 'NL'

# filings_api.to_sqlite
# filings_api.filing_page_iter
