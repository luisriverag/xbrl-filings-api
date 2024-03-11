"""
Define tests for `ResourceCollection`.

The tests for the method `get_pandas_data` are in separate module
``test_pandas_data``.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api as xf


@pytest.fixture
def oldest3_fi_filingset(oldest3_fi_response):
    """FilingSet from mock response ``oldest3_fi``."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ONLY_FILINGS,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_entities_filingset(oldest3_fi_entities_response):
    """FilingSet from mock response ``oldest3_fi_entities`` with entities."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_ENTITY,
        add_api_params=None
        )


@pytest.fixture
def oldest3_fi_vmessages_filingset(oldest3_fi_vmessages_response):
    """FilingSet from mock response ``oldest3_fi_vmessages`` with validation messages."""
    return xf.get_filings(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=xf.GET_VALIDATION_MESSAGES,
        add_api_params=None
        )


@pytest.fixture
def asml22en_entities_filingset(asml22en_entities_response, res_colls):
    """FilingSet from mock response ``asml22en_entities``."""
    return xf.get_filings(
        filters={'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'},
        sort=None,
        max_size=1,
        flags=xf.GET_ENTITY,
        add_api_params=None
        )


def test_no_subresources(oldest3_fi_filingset):
    """Test FilingsSet with empty sets in ResourceCollection."""
    fs: xf.FilingSet = oldest3_fi_filingset
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert fs.entities.exist is False
    assert len(fs.entities) == 0
    ent_iter = iter(fs.entities)
    with pytest.raises(StopIteration):
        next(ent_iter)
    assert isinstance(fs.entities.columns, list)
    assert fs.entities.filingset is fs

    assert isinstance(fs.validation_messages, xf.ResourceCollection)
    assert fs.validation_messages.exist is False
    assert len(fs.validation_messages) == 0
    msg_iter = iter(fs.validation_messages)
    with pytest.raises(StopIteration):
        next(msg_iter)
    assert isinstance(fs.validation_messages.columns, list)
    assert fs.validation_messages.filingset is fs


def test_with_entities(oldest3_fi_entities_filingset):
    """Test FilingsSet with entities but no validation messages."""
    fs: xf.FilingSet = oldest3_fi_entities_filingset
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert fs.entities.exist is True
    assert len(fs.entities) == 3
    all_ents = []
    for ent in fs.entities:
        assert isinstance(ent, xf.Entity)
        all_ents.append(ent)
    for ent in all_ents:
        assert ent in fs.entities
    assert isinstance(fs.entities.columns, list)
    for col in fs.entities.columns:
        assert isinstance(col, str)
    assert fs.entities.filingset is fs

    assert isinstance(fs.validation_messages, xf.ResourceCollection)
    assert fs.validation_messages.exist is False
    assert len(fs.validation_messages) == 0
    msg_iter = iter(fs.validation_messages)
    with pytest.raises(StopIteration):
        next(msg_iter)
    assert isinstance(fs.validation_messages.columns, list)
    assert fs.validation_messages.filingset is fs


def test_with_vmessages(oldest3_fi_vmessages_filingset):
    """Test FilingsSet with validation messages but no entities."""
    fs: xf.FilingSet = oldest3_fi_vmessages_filingset
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert fs.entities.exist is False
    assert len(fs.entities) == 0
    ent_iter = iter(fs.entities)
    with pytest.raises(StopIteration):
        next(ent_iter)
    assert isinstance(fs.entities.columns, list)
    assert fs.entities.filingset is fs

    assert isinstance(fs.validation_messages, xf.ResourceCollection)
    assert fs.validation_messages.exist is True
    assert len(fs.validation_messages) > 0
    all_vmsgs = []
    for vmsg in fs.validation_messages:
        assert isinstance(vmsg, xf.ValidationMessage)
        all_vmsgs.append(vmsg)
    for vmsg in all_vmsgs:
        assert vmsg in fs.validation_messages
    assert isinstance(fs.validation_messages.columns, list)
    for col in fs.validation_messages.columns:
        assert isinstance(col, str)
    assert fs.validation_messages.filingset is fs


def test_add_entities(oldest3_fi_entities_filingset, asml22en_entities_filingset):
    """Test FilingsSet with entities which will be updated with more filings and entities."""
    fs: xf.FilingSet = oldest3_fi_entities_filingset
    fs_add: xf.FilingSet = asml22en_entities_filingset
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert fs.entities.exist is True
    assert len(fs.entities) == 3
    before_ents = []
    for ent in fs.entities:
        assert isinstance(ent, xf.Entity)
        before_ents.append(ent)
    for ent in before_ents:
        assert ent in fs.entities
    assert isinstance(fs.entities.columns, list)
    before_cols = []
    for col in fs.entities.columns:
        assert isinstance(col, str)
        before_cols.append(col)

    fs.update(fs_add)
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert fs.entities.exist is True
    assert len(fs.entities) == 4
    after_ents = before_ents.copy()
    for ent in fs.entities:
        assert isinstance(ent, xf.Entity)
        after_ents.append(ent)
    for ent in after_ents:
        assert ent in fs.entities
    assert isinstance(fs.entities.columns, list)
    after_cols = []
    for col in fs.entities.columns:
        assert isinstance(col, str)
        after_cols.append(col)
    for col in before_cols:
        assert col in after_cols
