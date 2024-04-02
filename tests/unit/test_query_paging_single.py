"""Define tests for handling of filing pages in query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import pytest

import xbrl_filings_api as xf


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
    received_api_ids = set(page1_filings + page2_filings)
    assert len(received_api_ids) == 4, 'Receive 4 unique api_id values'


@pytest.mark.paging
def test_removing_extra_entities(
        estonian_2_pages_3_each_response, monkeypatch):
    """
    Test 2 pages, size 3, of 4 filings for entity reference coherence.
    """
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
    # `Entity.api_id` values from FilingsPage.entity_list
    p1_ent_ids_incl = [ent.api_id for ent in page1.entity_list]
    msg1 = 'FilingsPage.entity_list items have unique api_id values on page {}'
    assert len(p1_ent_ids_incl) == len(set(p1_ent_ids_incl)), msg1.format(1)
    # `Entity.api_id` values from backreferences in Filing.entity
    p1_ent_ids_ref = [
        filing.entity.api_id for filing in page1.filing_list]
    msg2 = (
        'Filing.entity backreference api_id values match '
        'FilingsPage.entity_list on page {}'
        )
    assert set(p1_ent_ids_incl) == set(p1_ent_ids_ref), msg2.format(1)

    page2 = next(piter)
    # `Entity.api_id` values from FilingsPage.entity_list
    p2_ent_ids_incl = [ent.api_id for ent in page2.entity_list]
    assert len(p2_ent_ids_incl) == len(set(p2_ent_ids_incl)), msg1.format(2)
    # `Entity.api_id` values from backreferences in Filing.entity
    p2_ent_ids_ref = [
        filing.entity.api_id for filing in page2.filing_list]
    assert set(p2_ent_ids_incl) == set(p2_ent_ids_ref), msg2.format(2)


@pytest.mark.paging
def test_removing_extra_validation_messages(
        estonian_2_pages_3_each_response, monkeypatch):
    """
    Test 2 pages, size 3, of 4 filings for validation message reference
    coherence.
    """
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
    # `ValidationMessage.api_id` values from
    # FilingsPage.validation_message_list
    p1_vm_ids_incl = [vm.api_id for vm in page1.validation_message_list]
    msg1 = (
        'FilingsPage.validation_message_list items have unique api_id '
        'values on page {}'
        )
    assert len(p1_vm_ids_incl) == len(set(p1_vm_ids_incl)), msg1.format(1)
    # `ValidationMessage.api_id` values from backreferences in
    # Filing.validation_messages
    p1_vm_ids_ref = []
    for filing in page1.filing_list:
        p1_vm_ids_ref.extend([vm.api_id for vm in filing.validation_messages])
    msg2 = (
        'Filing.validation_messages backreference have unique api_id '
        'values on page {}'
        )
    assert len(p1_vm_ids_ref) == len(set(p1_vm_ids_ref)), msg2.format(1)
    msg3 = (
        'Filing.validation_messages backreference api_id values match '
        'FilingsPage.validation_message_list on page {}'
        )
    assert set(p1_vm_ids_incl) == set(p1_vm_ids_ref), msg3.format(1)

    page2 = next(piter)
    # `ValidationMessage.api_id` values from
    # FilingsPage.validation_message_list
    p2_vm_ids_incl = [vm.api_id for vm in page2.validation_message_list]
    assert len(p2_vm_ids_incl) == len(set(p2_vm_ids_incl)), msg1.format(2)
    # `ValidationMessage.api_id` values from backreferences in
    # Filing.validation_messages
    p2_vm_ids_ref = []
    for filing in page2.filing_list:
        p2_vm_ids_ref.extend([vm.api_id for vm in filing.validation_messages])
    assert len(p2_vm_ids_ref) == len(set(p2_vm_ids_ref)), msg2.format(2)
    assert set(p2_vm_ids_incl) == set(p2_vm_ids_ref), msg3.format(2)
