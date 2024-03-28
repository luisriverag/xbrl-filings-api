"""Define tests for superclass `set` operations of `FilingSet`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import re

import pytest
import responses

import xbrl_filings_api as xf

pytestmark = pytest.mark.skip(reason='Not yet implemented')


@pytest.fixture
def stellantis21to22_filingset(urlmock):
    """FilingSet for Stellantis 2021 to 2022 filings with entity."""
    stellantis_api_ids = ['1034', '4325']
    fs = None
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'stellantis21to22')
        fs = xf.get_filings(
            filters={'api_id': stellantis_api_ids},
            sort=None,
            max_size=2,
            flags=xf.GET_ENTITY
            )
    return fs


@pytest.fixture
def stellantis23_filingset(urlmock):
    """FilingSet for Stellantis 2023 filings with entity."""
    fs = None
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'stellantis23')
        fs = xf.get_filings(
            filters={'api_id': '12398'},
            sort=None,
            max_size=1,
            flags=xf.GET_ENTITY
            )
    return fs


@pytest.fixture
def stellantis22to23_filingset(urlmock):
    """FilingSet for Stellantis 2022 to 2023 filings with entity."""
    stellantis_api_ids = ['4325', '12398']
    fs = None
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'stellantis22to23')
        fs = xf.get_filings(
            filters={'api_id': stellantis_api_ids},
            sort=None,
            max_size=2,
            flags=xf.GET_ENTITY
            )
    return fs


@pytest.mark.parametrize('method', [
    'union',
    '__or__',
    'update',
    '__ior__',
    ])
def test_union(
        method, stellantis21to22_filingset, stellantis22to23_filingset):
    """Test union operation."""
    fs_21_22: xf.FilingSet = stellantis21to22_filingset # Left operand
    fs_22_23: xf.FilingSet = stellantis22to23_filingset # Right operand
    if method == 'union':
        fs_result = fs_21_22.union(fs_22_23)
    elif method == '__or__':
        fs_result = fs_21_22 | fs_22_23
    elif method == 'update':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result.update(fs_22_23)
    elif method == '__ior__':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result |= fs_22_23

    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 3

    ids_result = [f.api_id for f in fs_result]
    ids_21_22_23 = {'1034', '4325', '12398'}
    assert set(ids_result) == ids_21_22_23

    fs_result_ents = {f.entity for f in fs_result}
    assert len(fs_result_ents) == 1
    ent_result: xf.Entity = next(iter(fs_result_ents))
    ent_21_22 = next(iter(fs_21_22.entities))
    ent_22_23 = next(iter(fs_22_23.entities))
    if method in ('union', '__or__'):
        assert ent_result is not ent_21_22, 'New Entity created'
    if method in ('update', '__ior__'):
        assert ent_result is ent_21_22, 'Entity retained from left side'
    assert ent_result is not ent_22_23, 'Entity dropped from right side'

    assert len(ent_result.filings) == 3
    ent_result_backref_ids = {f.api_id for f in ent_result.filings}
    assert ent_result_backref_ids == ids_21_22_23


@pytest.mark.parametrize('method', [
    'intersection',
    '__and__',
    'intersection_update',
    '__iand__',
    ])
def test_intersection(
        method, stellantis21to22_filingset, stellantis22to23_filingset):
    """Test intersection operation."""
    fs_21_22: xf.FilingSet = stellantis21to22_filingset # Left operand
    fs_22_23: xf.FilingSet = stellantis22to23_filingset # Right operand
    if method == 'intersection':
        fs_result = fs_21_22.intersection(fs_22_23)
    elif method == '__and__':
        fs_result = fs_21_22 & fs_22_23
    elif method == 'intersection_update':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result.intersection_update(fs_22_23)
    elif method == '__iand__':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result &= fs_22_23

    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 1

    id_22 = '4325'
    ids_result = [f.api_id for f in fs_result]
    assert ids_result[0] == id_22

    fs_result_ents = {f.entity for f in fs_result}
    assert len(fs_result_ents) == 1
    ent_result: xf.Entity = next(iter(fs_result_ents))
    ent_21_22 = next(iter(fs_21_22.entities))
    ent_22_23 = next(iter(fs_22_23.entities))
    if method in ('intersection', '__and__'):
        assert ent_result is not ent_21_22, 'New Entity created'
    if method in ('intersection_update', '__iand__'):
        assert ent_result is ent_21_22, 'Entity retained from left side'
    assert ent_result is not ent_22_23, 'Entity dropped from right side'

    assert len(ent_result.filings) == 1
    ent_result_backref: xf.Filing = next(iter(ent_result.filings))
    assert ent_result_backref.api_id == id_22


@pytest.mark.parametrize('method', [
    'difference',
    '__sub__',
    'difference_update',
    '__isub__',
    ])
def test_difference(
        method, stellantis21to22_filingset, stellantis22to23_filingset):
    """Test difference operation."""
    fs_21_22: xf.FilingSet = stellantis21to22_filingset # Left operand
    fs_22_23: xf.FilingSet = stellantis22to23_filingset # Right operand
    if method == 'difference':
        fs_result = fs_21_22.difference(fs_22_23)
    elif method == '__sub__':
        fs_result = fs_21_22 - fs_22_23
    elif method == 'difference_update':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result.difference_update(fs_22_23)
    elif method == '__isub__':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result -= fs_22_23

    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 1

    id_21 = '1034'
    ids_result = [f.api_id for f in fs_result]
    assert ids_result[0] == id_21

    fs_result_ents = {f.entity for f in fs_result}
    assert len(fs_result_ents) == 1
    ent_result: xf.Entity = next(iter(fs_result_ents))
    ent_21_22 = next(iter(fs_21_22.entities))
    ent_22_23 = next(iter(fs_22_23.entities))
    if method in ('difference', '__sub__'):
        assert ent_result is not ent_21_22, 'New Entity created'
    if method in ('difference_update', '__isub__'):
        assert ent_result is ent_21_22, 'Entity retained from left side'
    assert ent_result is not ent_22_23, 'Entity dropped from right side'

    assert len(ent_result.filings) == 1
    ent_result_backref: xf.Filing = next(iter(ent_result.filings))
    assert ent_result_backref.api_id == id_21


@pytest.mark.parametrize('method', [
    'symmetric_difference',
    '__xor__',
    'symmetric_difference_update',
    '__ixor__',
    ])
def test_symmetric_difference(
        method, stellantis21to22_filingset, stellantis22to23_filingset):
    """Test symmetric_difference operation."""
    fs_21_22: xf.FilingSet = stellantis21to22_filingset # Left operand
    fs_22_23: xf.FilingSet = stellantis22to23_filingset # Right operand
    if method == 'symmetric_difference':
        fs_result = fs_21_22.symmetric_difference(fs_22_23)
    elif method == '__xor__':
        fs_result = fs_21_22 ^ fs_22_23
    elif method == 'symmetric_difference_update':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result.symmetric_difference_update(fs_22_23)
    elif method == '__ixor__':
        fs_result = xf.FilingSet(fs_21_22)
        fs_result ^= fs_22_23

    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 2

    ids_21_23 = {'1034', '12398'}
    ids_result = {f.api_id for f in fs_result}
    assert ids_result == ids_21_23

    fs_result_ents = {f.entity for f in fs_result}
    assert len(fs_result_ents) == 1
    ent_result: xf.Entity = next(iter(fs_result_ents))
    ent_21_22 = next(iter(fs_21_22.entities))
    ent_22_23 = next(iter(fs_22_23.entities))
    if method in ('symmetric_difference', '__xor__'):
        assert ent_result is not ent_21_22, 'New Entity created'
    if method in ('symmetric_difference_update', '__ixor__'):
        assert ent_result is ent_21_22, 'Entity retained from left side'
    assert ent_result is not ent_22_23, 'Entity dropped from right side'

    assert len(ent_result.filings) == 2
    ent_result_backref_ids = {f.api_id for f in ent_result.filings}
    assert ent_result_backref_ids == ids_21_23


@pytest.mark.parametrize('method', [
    'union',
    '__or__',
    'update',
    '__ior__',
    'intersection',
    '__and__',
    'intersection_update',
    '__iand__',
    'difference',
    '__sub__',
    'difference_update',
    '__isub__',
    'symmetric_difference',
    '__xor__',
    'symmetric_difference_update',
    '__ixor__',
    ])
def test_raise_bad_iterable(
        method, stellantis21to22_filingset, stellantis22to23_filingset):
    """Test union when iterable has non-Filing items."""
    fs_21_22: xf.FilingSet = stellantis21to22_filingset # Left operand
    set_22_23: set[xf.Filing] = set(stellantis22to23_filingset) # Right operand
    kwargs = {}
    if not method.startswith('__'):
        kwargs = {'match': r'Arguments must be FilingSet objects.'}
    with pytest.raises(TypeError, **kwargs):
        method_callable = getattr(fs_21_22, method)
        method_callable(set_22_23)


def test_copy(stellantis23_filingset):
    """Test copy method."""
    fs: xf.FilingSet = stellantis23_filingset
    fs_copy = fs.copy()
    assert isinstance(fs_copy, xf.FilingSet)


def test_add_new(stellantis21to22_filingset, stellantis23_filingset):
    """Test add method with new item."""
    fs_result: xf.FilingSet = stellantis21to22_filingset
    fs_23: xf.FilingSet = stellantis23_filingset
    filing_23: xf.Filing = next(iter(fs_23))
    fs_result.add(filing_23) # Add 23 to {21, 22}
    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 3

    ids_result = {f.api_id for f in fs_result}
    e_filing_ids = {'1034', '4325', '12398'}
    assert ids_result == e_filing_ids

    ents_result = {f.entity for f in fs_result}
    assert len(ents_result) == 1
    ent_result: xf.Entity = next(iter(ents_result))

    assert len(ent_result.filings) == 3
    ent_result_backref_ids = {f.api_id for f in ent_result.filings}
    assert ent_result_backref_ids == e_filing_ids


def test_add_existing(stellantis21to22_filingset, stellantis22to23_filingset):
    """Test add method with already existing item with different identity."""
    fs_result: xf.FilingSet = stellantis21to22_filingset
    fs_22_23: xf.FilingSet = stellantis22to23_filingset
    filing_22: xf.Filing = next(filter(lambda f: f.api_id == '4325', fs_22_23))
    fs_result.add(filing_22) # Add 22 to {21, 22}
    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 2

    ids_result = {f.api_id for f in fs_result}
    e_filing_ids = {'1034', '4325'}
    assert ids_result == e_filing_ids
    filing_result_22: xf.Filing = next(filter(
        lambda f: f.api_id == '4325', fs_result))
    assert filing_result_22 is not filing_22, 'Same filing not added'

    ents_result = {f.entity for f in fs_result}
    assert len(ents_result) == 1
    ent_result: xf.Entity = next(iter(ents_result))

    assert len(ent_result.filings) == 2
    ent_result_backref_ids = {f.api_id for f in ent_result.filings}
    assert ent_result_backref_ids == e_filing_ids


def test_add_raise_wrong_type(
        stellantis21to22_filingset, stellantis22to23_filingset):
    """Test add method by adding an Entity to it."""
    fs_result: xf.FilingSet = stellantis21to22_filingset
    fs_22_23: xf.FilingSet = stellantis22to23_filingset
    ent_22_23: xf.Entity = next(iter(fs_22_23.entities))
    with pytest.raises(
            TypeError, match=r'FilingSet can only contain Filing objects'):
        fs_result.add(ent_22_23)
    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 2


@pytest.mark.parametrize('method', ['remove', 'discard'])
def test_remove_success(method, stellantis22to23_filingset, stellantis23_filingset):
    """Test remove/discard method with new item."""
    fs_result: xf.FilingSet = stellantis22to23_filingset
    fs_23: xf.FilingSet = stellantis23_filingset
    filing_23: xf.Filing = next(iter(fs_23))
    method_callable = getattr(fs_result, method)
    method_callable(filing_23) # Remove 23 to {22, 23}
    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 1

    ids_result = {f.api_id for f in fs_result}
    id_22 = '4325'
    assert ids_result[0] == id_22

    ents_result = {f.entity for f in fs_result}
    assert len(ents_result) == 1
    ent_result: xf.Entity = next(iter(ents_result))

    assert len(ent_result.filings) == 1
    ent_result_backref_ids = [f.api_id for f in ent_result.filings]
    assert ent_result_backref_ids[0] == id_22


def test_remove_missing(stellantis21to22_filingset, stellantis23_filingset):
    """Test remove method by removing an item not present."""
    fs_result: xf.FilingSet = stellantis21to22_filingset
    fs_23: xf.FilingSet = stellantis23_filingset
    filing_23: xf.Entity = next(iter(fs_23))
    with pytest.raises(KeyError, match=re.escape(repr(filing_23))):
        fs_result.remove(filing_23)
    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 2


def test_discard_missing(stellantis21to22_filingset, stellantis23_filingset):
    """Test discard method by removing an item not present."""
    fs_result: xf.FilingSet = stellantis21to22_filingset
    fs_23: xf.FilingSet = stellantis23_filingset
    filing_23: xf.Entity = next(iter(fs_23))
    fs_result.discard(filing_23)
    assert isinstance(fs_result, xf.FilingSet)
    assert len(fs_result) == 2


def test_pop(stellantis21to22_filingset):
    """Test pop method."""
    fs_result: xf.FilingSet = stellantis21to22_filingset
    filing = fs_result.pop()
    assert isinstance(fs_result, xf.FilingSet)
    assert isinstance(filing, xf.Filing)
    assert len(fs_result) == 1

    ent_result: xf.Entity = next(iter(fs_result.entities))
    assert len(ent_result.filings) == 1
