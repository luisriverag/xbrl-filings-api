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


@pytest.fixture
def multipage_2nd_filingspage(multipage_lax_response, res_colls, monkeypatch):
    """FilingsPage for the second `multipage` mock URL response."""
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
def test_attributes(multipage_2nd_filingspage):
    """Test _APIPage attributes."""
    fpage: xf.FilingsPage = multipage_2nd_filingspage
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
                    'links': { 'related': '/api/alien_types/724500Y6DUVHQD6OXN27' },
                    'data': { 'type': 'alien_type', 'id': '123456789'}
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
            'links': { 'self': '/api/alien_types/123456789' }
        }],
        'links': {
            'self': 'https://filings.xbrl.org/api/filings'
            },
        'meta': { 'count': 1 },
        'jsonapi': { 'version': '1.0' }
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
