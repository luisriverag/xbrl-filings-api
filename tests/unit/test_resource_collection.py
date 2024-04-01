"""
Define tests for `ResourceCollection`.

The tests for the method `get_pandas_data` are in separate module
``test_pandas_data``.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import copy

import pytest

import xbrl_filings_api as xf


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


def test_no_subresources(get_oldest3_fi_filingset):
    """Test FilingsSet with empty sets in ResourceCollection."""
    fs: xf.FilingSet = get_oldest3_fi_filingset()
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


def test_with_entities(get_oldest3_fi_entities_filingset):
    """Test FilingsSet with entities but no validation messages."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    assert isinstance(fs.entities, xf.ResourceCollection)
    assert fs.entities.exist is True
    assert len(fs.entities) == 3
    iter_entities = []
    for ent in fs.entities:
        assert isinstance(ent, xf.Entity)
        iter_entities.append(ent)
    for iter_entity in iter_entities:
        assert iter_entity in fs.entities
    for filing in fs:
        assert filing.entity in fs.entities
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


def test_with_vmessages(get_oldest3_fi_vmessages_filingset):
    """Test FilingsSet with validation messages but no entities."""
    fs: xf.FilingSet = get_oldest3_fi_vmessages_filingset()
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
    iter_vmsgs = []
    for vmsg in fs.validation_messages:
        assert isinstance(vmsg, xf.ValidationMessage)
        iter_vmsgs.append(vmsg)
    for vmsg in iter_vmsgs:
        assert vmsg in fs.validation_messages
    for filing in fs:
        for e_vmsg in filing.validation_messages:
            assert e_vmsg in fs.validation_messages
    assert isinstance(fs.validation_messages.columns, list)
    for col in fs.validation_messages.columns:
        assert isinstance(col, str)
    assert fs.validation_messages.filingset is fs


def test_add_entities(get_oldest3_fi_entities_filingset, asml22en_entities_filingset):
    """Test FilingsSet with entities which will be updated with more filings and entities."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
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
    for filing in fs:
        assert filing.entity in fs.entities
    assert isinstance(fs.entities.columns, list)
    after_cols = []
    for col in fs.entities.columns:
        assert isinstance(col, str)
        after_cols.append(col)

    for col in before_cols:
        assert col in after_cols


def test_same_entity_only_once(kone22_all_languages_response):
    """Test same entity is in the collection only once."""
    fs = xf.get_filings(
        filters={'api_id': ['4143', '4144']},
        sort=None,
        max_size=100,
        flags=xf.GET_ENTITY
        )
    assert len(fs) == 2
    assert fs.entities.exist
    assert len(fs.entities) == 1
    ents = list(fs.entities)
    assert len(ents) == 1


def test_repr_entities(get_oldest3_fi_entities_filingset):
    """Test `__repr__` for entity ResourceCollection."""
    e_repr = (
        "ResourceCollection("
        "item_class=<class 'xbrl_filings_api.entity.Entity'>, len()=3)"
        )
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    assert repr(fs.entities) == e_repr


def test_repr_vmessages(get_oldest3_fi_vmessages_filingset):
    """Test `__repr__` for validation message ResourceCollection."""
    e_repr = (
        "ResourceCollection(item_class=<class "
        "'xbrl_filings_api.validation_message.ValidationMessage'>, len()=45)"
        )
    fs: xf.FilingSet = get_oldest3_fi_vmessages_filingset()
    assert repr(fs.validation_messages) == e_repr


def test_contains_is_true_diff_identities(get_oldest3_fi_entities_filingset):
    """Test `in` operator evaluates to True if filing is same but identity different."""
    fs_a: xf.FilingSet = get_oldest3_fi_entities_filingset()
    fs_b: xf.FilingSet = get_oldest3_fi_entities_filingset()
    ent_a = next(iter(fs_a.entities))
    assert ent_a in fs_b.entities


def test_contains_is_false_wrong_type(get_oldest3_fi_entities_filingset):
    """Test `in` operator evaluates to False when wrong type."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    filing = next(iter(fs))
    assert filing not in fs.entities


def test_contains_is_true_hash_tuple_api_id(get_oldest3_fi_entities_filingset):
    """Test `in` operator evaluates to True when compared with hash tuple."""
    fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
    ent = next(iter(fs)).entity
    hash_tuple = ('APIResource', xf.Entity.TYPE, ent.api_id)
    assert hash_tuple in fs.entities
