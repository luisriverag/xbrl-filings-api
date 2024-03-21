"""Define tests for `_APIPage`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import re
import urllib.parse
from datetime import datetime

import pytest
import responses

import xbrl_filings_api as xf
from xbrl_filings_api.api_page import _APIPage, _IncludedResource
from xbrl_filings_api.api_request import _APIRequest


@pytest.fixture
def paging_swedish_size2_pg3_2nd_filingspage(paging_swedish_size2_pg3_lax_response, res_colls, monkeypatch):
    """FilingsPage for 2nd page (2pc) of oldest Swedish filings."""
    monkeypatch.setattr(xf.options, 'max_page_size', 2)
    piter = xf.filing_page_iter(
        filters={
            'country': 'SE'
            },
        sort='added_time',
        max_size=5,
        flags=xf.GET_ONLY_FILINGS
        )
    next(piter)
    return next(piter)


@pytest.fixture
def oldest3_fi_entities_filingspage(oldest3_fi_entities_response):
    """FilingPage from mock response ``oldest3_fi_entities`` with entities."""
    piter = xf.filing_page_iter(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ENTITY,
        add_api_params=None
        )
    return next(piter)


@pytest.mark.paging
def test_attributes(paging_swedish_size2_pg3_2nd_filingspage):
    """Test _APIPage attributes."""
    fpage: xf.FilingsPage = paging_swedish_size2_pg3_2nd_filingspage
    assert isinstance(fpage, _APIPage)
    def pmatch(s, isbigpage=False):
        return (
            r'https://filings\.xbrl\.org/api/filings\?.*'
            + urllib.parse.quote(s, '=')
            + (r'\d{2,}' if isbigpage else '')
            )
    assert re.search(f"{pmatch('page[number]=2')}", fpage.api_self_url)
    assert re.search(f"{pmatch('')}", fpage.api_prev_page_url)
    assert re.search(f"{pmatch('page[number]=3')}", fpage.api_next_page_url)
    assert re.search(f"{pmatch('')}", fpage.api_first_page_url)
    assert re.search(f"{pmatch('page[number]=', True)}", fpage.api_last_page_url)
    assert fpage.jsonapi_version == '1.0'
    assert type(fpage.query_time) is datetime
    assert re.search(f"{pmatch('')}", fpage.request_url)
    assert isinstance(fpage._data, list)
    assert isinstance(fpage._included_resources, list)
    for inc_res in fpage._included_resources:
        assert isinstance(inc_res, _IncludedResource)
    assert fpage._data_count > 10


def test_included_resources(oldest3_fi_entities_filingspage):
    """Test attribute `_included_resources`."""
    fpage: xf.FilingsPage = oldest3_fi_entities_filingspage
    assert isinstance(fpage._included_resources, list)
    for inc_res in fpage._included_resources:
        assert inc_res.type_ == 'entity'
        assert isinstance(inc_res.id_, str)
        assert isinstance(inc_res.frag, dict)


def test_included_resources_unexpected():
    """Test attribute `_included_resources` with unexpected type."""
    rsps_with_alien_type = {
        'data': [{
            'type': 'filing',
            'attributes': {
                'fxo_id': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
                'package_url': '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en.zip'
                },
            'relationships': {
                'alien_type': {
                    'links': {'related': '/api/alien_types/724500Y6DUVHQD6OXN27'},
                    'data': {'type': 'alien_type', 'id': '123456789'}
                    }
                },
            'id': '4261',
            'links': { 'self': '/api/filings/4261' }
            }],
        'included': [{
            'type': 'alien_type',
            'id': '123456789',
            'attributes': {},
            'relationships': {},
            'links': {'self': '/api/alien_types/123456789'}
        }],
        'links': {
            'self': 'https://filings.xbrl.org/api/filings'
            },
        'meta': {'count': 1},
        'jsonapi': {'version': '1.0'}
        }
    fpage: xf.FilingsPage
    with responses.RequestsMock() as rsps:
        rsps.add(
            method='GET',
            url=re.compile(r'.+'),
            json=rsps_with_alien_type,
        )
        piter = xf.filing_page_iter()
        fpage = next(piter)
    assert isinstance(fpage._included_resources, list)
    alien_res = fpage._included_resources[0]
    assert alien_res.type_ == 'alien_type'
    assert alien_res.id_ == '123456789'
    assert isinstance(alien_res.frag, dict)


def test_raises_initiate_directly():
    """Test _APIPage raises if initiated directly from parent class."""
    rsps_dummy = {
        'data': [],
        'links': {
            'self': 'https://filings.xbrl.org/api/filings'
            },
        'meta': { 'count': 0 },
        'jsonapi': { 'version': '1.0' }
        }
    areq = _APIRequest(
        url='https://filings.xbrl.org/api/filings',
        query_time=datetime.now()
        )
    with pytest.raises(
            NotImplementedError,
            match=r'_APIPage can only be initialized via subclassing'):
        _ = _APIPage(
            json_frag=rsps_dummy,
            api_request=areq
            )


def test_main_resource_api_id_as_int():
    """Test filing api_id from API as int."""
    rsps_with_int_data_id = {
        'data': [{
            'type': 'filing',
            'attributes': {
                'fxo_id': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
                'package_url': '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en.zip'
                },
            'relationships': {
                'entity': {
                    'links': {'related': '/api/entities/724500Y6DUVHQD6OXN27'},
                    'data': {'type': 'entity', 'id': '123456789'}
                    }
                },
            'id': 123,
            'links': {'self': '/api/filings/123'}
            }],
        'links': {
            'self': 'https://filings.xbrl.org/api/filings'
            },
        'meta': {'count': 0},
        'jsonapi': {'version': '1.0'}
        }
    fpage: xf.FilingsPage
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=re.compile(r'.+'),
            json=rsps_with_int_data_id,
        )
        piter = xf.filing_page_iter()
        fpage = next(piter)
    assert len(fpage._data) == 1
    filing_frag = fpage._data[0]
    assert filing_frag['id'] == '123'
    assert filing_frag['attributes']['fxo_id'] == '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'


def test_included_resource_api_id_as_int():
    """Test filing api_id from API as int."""
    rsps_with_int_included_id = {
        'data': [{
            'type': 'filing',
            'attributes': {
                'fxo_id': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
                'package_url': '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en.zip'
                },
            'relationships': {
                'entity': {
                    'links': {'related': '/api/entities/724500Y6DUVHQD6OXN27'},
                    'data': {'type': 'entity', 'id': 123456789}
                    }
                },
            'id': '123',
            'links': {'self': '/api/filings/123'}
            }],
        'included': [{
            'type': 'entity',
            'id': 123456789,
            'attributes': {},
            'relationships': {},
            'links': {'self': '/api/entities/123456789'}
        }],
        'links': {
            'self': 'https://filings.xbrl.org/api/filings'
            },
        'meta': {'count': 0},
        'jsonapi': {'version': '1.0'}
        }
    fpage: xf.FilingsPage
    with responses.RequestsMock() as rsps:
        rsps.get(
            url=re.compile(r'.+'),
            json=rsps_with_int_included_id,
        )
        piter = xf.filing_page_iter()
        fpage = next(piter)
    assert len(fpage._included_resources) == 1
    ent_frag = fpage._included_resources[0]
    assert ent_frag.id_ == '123456789'
    assert ent_frag.frag['links']['self'] == '/api/entities/123456789'
