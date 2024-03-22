"""Define tests for handling of filing pages in query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

from itertools import chain

import pytest
import requests

import xbrl_filings_api as xf


@pytest.mark.paging
@pytest.mark.xfail(
    reason=(
        'Error in undelying API: redundant filings on pages. '
        'Filing with api_id "1" (Cloetta AB, 2021, en) and "2" '
        '(Cloetta AB, 2021, sv) is returned twice and as a result, '
        'a fouth page is requested to fulfil expected 5 filings.'
        )
    )
def test_filing_page_iter(paging_swedish_size2_pg3_lax_response, monkeypatch):
    """Requested filings are available on 3 pages."""
    monkeypatch.setattr(xf.options, 'max_page_size', 2)
    piter = xf.filing_page_iter(
        filters={
            'country': 'SE'
            },
        sort='added_time',
        max_size=5,
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


@pytest.mark.date
@pytest.mark.paging
def test_no_limit(paging_czechia20dec_response, monkeypatch):
    """Requested filings are available on 3 pages."""
    monkeypatch.setattr(xf.options, 'max_page_size', 10)
    # The database has 29 records for this query
    fs = xf.get_filings(
        filters={
            'country': 'CZ',
            'last_end_date': '2020-12-31',
            },
        sort=None,
        max_size=xf.NO_LIMIT,
        flags=xf.GET_ONLY_FILINGS
        )
    assert len(fs) >= 29


@pytest.mark.paging
def test_removing_extra_filings(estonian_2_pages_3_each_response, monkeypatch):
    """Test getting 4 filings on 3 item pages, removing 2 from last."""
    monkeypatch.setattr(xf.options, 'max_page_size', 3)
    piter = xf.filing_page_iter(
        filters={
            'country': 'EE',
            },
        sort=None,
        max_size=4,
        flags=xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES
        )
    page1_filings = next(piter).filing_list
    assert len(page1_filings) == 3
    page2_filings = next(piter).filing_list
    assert len(page2_filings) == 1, 'Remove 2 unnecessary filings'
    assert next(piter, None) is None
    received_api_ids = set(chain(page1_filings, page2_filings))
    assert len(received_api_ids) == 4, 'Receive 4 unique api_id values'


@pytest.mark.paging
def test_removing_extra_entities(
        estonian_2_pages_3_each_response, monkeypatch):
    """Test 2 pages, size 3, of 4 filings for entity reference coherence."""
    monkeypatch.setattr(xf.options, 'max_page_size', 3)
    piter = xf.filing_page_iter(
        filters={
            'country': 'EE',
            },
        sort=None,
        max_size=4,
        flags=xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES
        )
    page1 = next(piter)
    p1_ent_ids_included = [ent.api_id for ent in page1.entity_list]
    assert len(p1_ent_ids_included) == len(set(p1_ent_ids_included)), 'Are unique'
    p1_ent_ids_referenced = [filing.entity.api_id for filing in page1.filing_list]
    assert set(p1_ent_ids_included) == set(p1_ent_ids_referenced), 'All in both'

    page2 = next(piter)
    p2_ent_ids_included = [ent.api_id for ent in page2.entity_list]
    assert len(p2_ent_ids_included) == len(set(p2_ent_ids_included)), 'Are unique'
    p2_ent_ids_referenced = [filing.entity.api_id for filing in page2.filing_list]
    assert set(p2_ent_ids_included) == set(p2_ent_ids_referenced), 'All in both'


@pytest.mark.paging
def test_removing_extra_validation_messages(
        estonian_2_pages_3_each_response, monkeypatch):
    """Test 2 pages, size 3, of 4 filings for validation message reference coherence."""
    monkeypatch.setattr(xf.options, 'max_page_size', 3)
    piter = xf.filing_page_iter(
        filters={
            'country': 'EE',
            },
        sort=None,
        max_size=4,
        flags=xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES
        )
    page1 = next(piter)
    p1_vm_ids_included = [vm.api_id for vm in page1.validation_message_list]
    assert len(p1_vm_ids_included) == len(set(p1_vm_ids_included)), 'Are unique'
    p1_vm_ids_referenced = []
    for filing in page1.filing_list:
        p1_vm_ids_referenced.extend([vm.api_id for vm in filing.validation_messages])
    assert len(p1_vm_ids_referenced) == len(set(p1_vm_ids_referenced)), 'Are unique'
    assert set(p1_vm_ids_included) == set(p1_vm_ids_referenced), 'All in both'

    page2 = next(piter)
    p2_vm_ids_included = [vm.api_id for vm in page2.validation_message_list]
    assert len(p2_vm_ids_included) == len(set(p2_vm_ids_included)), 'Are unique'
    p2_vm_ids_referenced = []
    for filing in page2.filing_list:
        p2_vm_ids_referenced.extend([vm.api_id for vm in filing.validation_messages])
    assert len(p2_vm_ids_referenced) == len(set(p2_vm_ids_referenced)), 'Are unique'
    assert set(p2_vm_ids_included) == set(p2_vm_ids_referenced), 'All in both'
