"""
Define tests for superclass `set` operations of `FilingSet`.

Tests use two separate queries of 4 filings having 2 common filings.
Consequently, these 2 shared filings are represented by 4 objects, the
same filing represented by 2 objects with different identities.

In set operations, all APIResource objects are are considered the same
on `api_id` basis, not identity basis.

In operations creating a new set, all resource objects are deep copied,
because of cross-references. In operations editing an existing set, only
introduced resources are deep copied.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import re
from typing import Union

import pytest
import responses

import xbrl_filings_api as xf

pytestmark = pytest.mark.skip(reason='Not yet implemented')


ID_UPM21_EN, ID_UPM21_FI = '138', '137'
ID_UPM22_EN, ID_UPM22_FI = '4455', '4456'
ID_UPM23_EN, ID_UPM23_FI = '12499', '12500'

ID_STR_ALL = (
    (ID_UPM21_EN, '21en'),
    (ID_UPM21_FI, '21fi'),
    (ID_UPM22_EN, '22en'),
    (ID_UPM22_FI, '22fi'),
    (ID_UPM23_EN, '23en'),
    (ID_UPM23_FI, '23fi')
    )
"""
Tuple of `(api_id, desc_str)` tuples years 2021 to 2023 both languages,
ordered.
"""

UNION_METHODS = (
    'union', '__or__',
    'update', '__ior__'
    )
INTERSECTION_METHODS = (
    'intersection', '__and__',
    'intersection_update', '__iand__'
    )
DIFFERENCE_METHODS = (
    'difference', '__sub__',
    'difference_update', '__isub__'
    )
SYMMETRIC_DIFFERENCE_METHODS = (
    'symmetric_difference', '__xor__',
    'symmetric_difference_update', '__ixor__'
    )
BASIC_SET_OPERATION_METHODS = (
    *UNION_METHODS, *INTERSECTION_METHODS,
    *DIFFERENCE_METHODS, *SYMMETRIC_DIFFERENCE_METHODS
    )
BASIC_SET_OPERATION_EDIT_METHODS = (
    'update', '__ior__',
    'intersection_update', '__iand__',
    'difference_update', '__isub__',
    'symmetric_difference_update', '__ixor__'
    )
BASIC_SET_OPERATION_OPERATOR_METHODS = [
    v for v in BASIC_SET_OPERATION_METHODS if v.startswith('__')]
BASIC_SET_OPERATION_NORMAL_METHODS = [
    v for v in BASIC_SET_OPERATION_METHODS if not v.startswith('__')]
SIMPLE_METHODS = ('copy', 'add', 'remove', 'discard', 'pop')


@pytest.fixture
def upm21to22_filingset(urlmock):
    """FilingSet for UPM-Kymmene 2021, 2022 filings (en, fi) with entities."""
    upm21to22_ids = [ID_UPM21_EN, ID_UPM21_FI, ID_UPM22_EN, ID_UPM22_FI]
    fs = None
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'upm21to22')
        fs = xf.get_filings(
            filters={'api_id': upm21to22_ids},
            sort=None,
            max_size=4,
            flags=xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES
            )
    return fs


@pytest.fixture
def upm22to23_filingset(urlmock):
    """FilingSet for UPM-Kymmene 2022, 2023 filings (en, fi) with entities."""
    upm22to23_ids = [ID_UPM22_EN, ID_UPM22_FI, ID_UPM23_EN, ID_UPM23_FI]
    fs = None
    with responses.RequestsMock() as rsps:
        urlmock.apply(rsps, 'upm22to23')
        fs = xf.get_filings(
            filters={'api_id': upm22to23_ids},
            sort=None,
            max_size=4,
            flags=xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES
            )
    return fs


@pytest.fixture
def upm22en_filing(upm22to23_filingset):
    """Filing for UPM-Kymmene 2022 English from `upm22to23` filing with entity."""
    fs: xf.FilingSet = upm22to23_filingset
    filing = next(f for f in fs if f.api_id == ID_UPM22_EN)
    return filing


@pytest.fixture
def upm23en_filing(upm22to23_filingset):
    """Filing for UPM-Kymmene 2023 English from `upm22to23` filing with entity."""
    fs: xf.FilingSet = upm22to23_filingset
    filing = next(f for f in fs if f.api_id == ID_UPM23_EN)
    return filing


def _execute_operation(
        method: str, fs_left: xf.FilingSet,
        fs_right: Union[xf.FilingSet, None]):
    if method == 'union':
        fs_result = fs_left.union(fs_right)
    elif method == '__or__':
        fs_result = fs_left | fs_right
    elif method == 'update':
        fs_result = fs_left
        fs_result.update(fs_right)
    elif method == '__ior__':
        fs_result = fs_left
        fs_result |= fs_right
    elif method == 'intersection':
        fs_result = fs_left.intersection(fs_right)
    elif method == '__and__':
        fs_result = fs_left & fs_right
    elif method == 'intersection_update':
        fs_result = fs_left
        fs_result.intersection_update(fs_right)
    elif method == '__iand__':
        fs_result = fs_left
        fs_result &= fs_right
    elif method == 'difference':
        fs_result = fs_left.difference(fs_right)
    elif method == '__sub__':
        fs_result = fs_left - fs_right
    elif method == 'difference_update':
        fs_result = fs_left
        fs_result.difference_update(fs_right)
    elif method == '__isub__':
        fs_result = fs_left
        fs_result -= fs_right
    elif method == 'symmetric_difference':
        fs_result = fs_left.symmetric_difference(fs_right)
    elif method == '__xor__':
        fs_result = fs_left ^ fs_right
    elif method == 'symmetric_difference_update':
        fs_result = fs_left
        fs_result.symmetric_difference_update(fs_right)
    elif method == '__ixor__':
        fs_result = fs_left
        fs_result ^= fs_right
    elif method == 'copy':
        fs_result = fs_left.copy()
    elif method == 'add':
        fs_result = fs_left
        fs_result.add(fs_right)
    elif method == 'remove':
        fs_result = fs_left
        fs_result.remove(fs_right)
    elif method == 'discard':
        fs_result = fs_left
        fs_result.discard(fs_right)
    elif method == 'pop':
        fs_result = fs_left
        fs_result.pop()
    return fs_result


def _build_ref_dict(
        filing_sets: list[tuple[Union[xf.FilingSet, set[object]], str]]
        ) -> dict[str, xf.Filing]:
    fil = {}
    for fs, fs_str in filing_sets:
        for match_id, desc_str in ID_STR_ALL:
            fil[f'{desc_str}_{fs_str}'] = next(
                (f for f in fs if f.api_id == match_id), None)
    return fil


def _get_right_operand(method: str, upm22to23_filingset: xf.FilingSet):
    if method in ('remove', 'discard'):
        # Included filing
        filing = next(f for f in upm22to23_filingset if f.api_id == ID_UPM22_EN)
        return filing
    elif method == 'add':
        # Excluded filing
        filing = next(f for f in upm22to23_filingset if f.api_id == ID_UPM23_EN)
        return filing
    elif method in ('copy', 'pop'):
        return None
    else:
        return upm22to23_filingset


##### Test basic set operations #####
# I.e., union, intersection, difference and symmetric_difference


@pytest.mark.parametrize('method', BASIC_SET_OPERATION_METHODS)
class TestBasicSetOperationFilingSet:
    """Test basic set operation FilingSet."""

    def test_filingset_type(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test union FilingSet type."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        assert isinstance(fs_result, xf.FilingSet)

    def test_filingset_copy_or_retain(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test union FilingSet identity."""
        isedit = method in BASIC_SET_OPERATION_EDIT_METHODS
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)

        if isedit:
            assert fs_result is fs_21_22, 'Left operand edited'
        else:
            assert fs_result is not fs_21_22, 'New FilingSet created'
        assert fs_result is not fs_22_23, 'Right operand left intact'

    def test_filing_deepcopy_or_retain(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Filing is retained (isedit=True, left) or deepcopied."""
        isedit = method in BASIC_SET_OPERATION_EDIT_METHODS
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)

        fil = _build_ref_dict([
            (fs_result, 'result'), (fs_21_22, '21_22'), (fs_22_23, '22_23')])
        if isedit:
            if fil['21en_result']:
                assert fil['21en_result'] is fil['21en_21_22'], (
                    'Filing 21en retained from left')
            if fil['21fi_result']:
                assert fil['21fi_result'] is fil['21fi_21_22'], (
                    'Filing 21fi retained from left')
            if fil['22en_result']:
                assert fil['22en_result'] is fil['22en_21_22'], (
                    'Shared 22en Filing retained from left')
            if fil['22fi_result']:
                assert fil['22fi_result'] is fil['22fi_21_22'], (
                    'Shared 22fi Filing retained from left')
            if fil['23en_result']:
                assert fil['23en_result'] is not fil['23en_22_23'], (
                    'Filing 23en (deep)copied from right')
            if fil['23fi_result']:
                assert fil['23fi_result'] is not fil['23fi_22_23'], (
                    'Filing 23fi (deep)copied from right')
        else:
            for fs_str in ('21_22', '22_23'):
                if fil['21en_result']:
                    assert fil['21en_result'] is not fil[f'21en_{fs_str}'], (
                        'Filing 21en (deep)copied')
                if fil['21fi_result']:
                    assert fil['21fi_result'] is not fil[f'21fi_{fs_str}'], (
                        'Filing 21fi (deep)copied')
                if fil['22en_result']:
                    assert fil['22en_result'] is not fil[f'22en_{fs_str}'], (
                        'Filing 22en (deep)copied')
                if fil['22fi_result']:
                    assert fil['22fi_result'] is not fil[f'22fi_{fs_str}'], (
                        'Filing 22fi (deep)copied')
                if fil['23en_result']:
                    assert fil['23en_result'] is not fil[f'23en_{fs_str}'], (
                        'Filing 23en (deep)copied')
                if fil['23fi_result']:
                    assert fil['23fi_result'] is not fil[f'23fi_{fs_str}'], (
                        'Filing 23fi (deep)copied')


@pytest.mark.parametrize('method', UNION_METHODS)
class TestUnion:
    """Test union operation with all four methods."""

    def test_filing_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test FilingSet item count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        msg = (
            '{21en, 21fi, 22en, 22fi} | {22en, 22fi, 23en, 23fi} '
            '== {21en, 21fi, 22en, 22fi, 23en, 23fi}, got len() == '
            f'{len(fs_result)}'
            )
        assert len(fs_result) == 6, msg

    def test_filing_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Filing.api_id values match expected."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        e_ids = {
            ID_UPM21_EN, ID_UPM21_FI, ID_UPM22_EN, ID_UPM22_FI,
            ID_UPM23_EN, ID_UPM23_FI
            }
        ids_result = {f.api_id for f in fs_result}
        assert ids_result == e_ids, 'Filing api_id values match expected'

    def test_entity_filings_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        assert len(ent_result.filings) == 6, 'As many backreferences as filings'

    def test_entity_filings_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings api_id are the same as for FilingSet."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        e_ids = {
            ID_UPM21_EN, ID_UPM21_FI, ID_UPM22_EN, ID_UPM22_FI,
            ID_UPM23_EN, ID_UPM23_FI
            }
        fil_ids_backref = {f.api_id for f in ent_result.filings}
        assert fil_ids_backref == e_ids, 'Entity.filings api_id values as expected'


@pytest.mark.parametrize('method', INTERSECTION_METHODS)
class TestIntersection:
    """Test intersection operation with all four methods."""

    def test_filing_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test FilingSet item count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        msg = (
            '{21en, 21fi, 22en, 22fi} & {22en, 22fi, 23en, 23fi} '
            '== {22en, 22fi}, got len() == '
            f'{len(fs_result)}'
            )
        assert len(fs_result) == 2, msg

    def test_filing_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Filing.api_id values match expected."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        e_ids = {ID_UPM22_EN, ID_UPM22_FI}
        ids_result = {f.api_id for f in fs_result}
        assert ids_result == e_ids, 'Filing api_id values match expected'

    def test_entity_filings_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        assert len(ent_result.filings) == 2, (
            'As many backreferences as filings')

    def test_entity_filings_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings api_id are the same as for FilingSet."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        e_ids = {ID_UPM22_EN, ID_UPM22_FI}
        fil_ids_backref = {f.api_id for f in ent_result.filings}
        assert fil_ids_backref == e_ids, (
            'Entity.filings api_id values as expected')


@pytest.mark.parametrize('method', DIFFERENCE_METHODS)
class TestDifference:
    """Test difference operation with all four methods."""

    def test_filing_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test FilingSet item count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        msg = (
            '{21en, 21fi, 22en, 22fi} - {22en, 22fi, 23en, 23fi} '
            '== {21en, 21fi}, got len() == '
            f'{len(fs_result)}'
            )
        assert len(fs_result) == 2, msg

    def test_filing_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Filing.api_id values match expected."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        e_ids = {ID_UPM21_EN, ID_UPM21_FI}
        ids_result = {f.api_id for f in fs_result}
        assert ids_result == e_ids, 'Filing api_id values match expected'

    def test_entity_filings_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        assert len(ent_result.filings) == 2, (
            'As many backreferences as filings')

    def test_entity_filings_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings api_id are the same as for FilingSet."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        e_ids = {ID_UPM21_EN, ID_UPM21_FI}
        fil_ids_backref = {f.api_id for f in ent_result.filings}
        assert fil_ids_backref == e_ids, (
            'Entity.filings api_id values as expected')


@pytest.mark.parametrize('method', SYMMETRIC_DIFFERENCE_METHODS)
class TestSymmetricDifference:
    """Test symmetric difference operation with all four methods."""

    def test_filing_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test FilingSet item count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        msg = (
            '{21en, 21fi, 22en, 22fi} ^ {22en, 22fi, 23en, 23fi} '
            '== {21en, 21fi, 23en, 23fi}, got len() == '
            f'{len(fs_result)}'
            )
        assert len(fs_result) == 4, msg

    def test_filing_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Filing.api_id values match expected."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        e_ids = {ID_UPM21_EN, ID_UPM21_FI, ID_UPM23_EN, ID_UPM23_FI}
        ids_result = {f.api_id for f in fs_result}
        assert ids_result == e_ids, 'Filing api_id values match expected'

    def test_entity_filings_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings count."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        assert len(ent_result.filings) == 4, (
            'As many backreferences as filings')

    def test_entity_filings_api_id(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings api_id are the same as for FilingSet."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        fs_22_23: xf.FilingSet = upm22to23_filingset # Right operand
        fs_result = _execute_operation(method, fs_21_22, fs_22_23)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        e_ids = {ID_UPM21_EN, ID_UPM21_FI, ID_UPM23_EN, ID_UPM23_FI}
        fil_ids_backref = {f.api_id for f in ent_result.filings}
        assert fil_ids_backref == e_ids, (
            'Entity.filings api_id values as expected')


@pytest.mark.parametrize('method', BASIC_SET_OPERATION_METHODS)
def test_raise_bad_iterable(
        method, upm21to22_filingset, upm22to23_filingset):
    """Test raising when iterable has non-Filing items."""
    fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
    list_22_23_str: list[xf.Filing] = list(upm22to23_filingset) # Right operand
    list_22_23_str.append('test') # Exception trigger
    with pytest.raises(
            ValueError,
            match=r'Arguments must be iterables of Filing objects.'):
        _ = _execute_operation(method, fs_21_22, list_22_23_str)


@pytest.mark.parametrize('method', BASIC_SET_OPERATION_NORMAL_METHODS)
def test_raise_not_iterable_normal_method(
        method, upm21to22_filingset, upm23en_filing):
    """Test raising when argument is not iterable."""
    fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
    filing_22en: xf.Filing = upm23en_filing # Right operand
    with pytest.raises(TypeError, match=r"'Filing' object is not iterable"):
        _ = _execute_operation(method, fs_21_22, filing_22en)


@pytest.mark.parametrize('method', BASIC_SET_OPERATION_OPERATOR_METHODS)
def test_raise_not_iterable_operator(
        method, upm21to22_filingset, upm23en_filing):
    """Test raising when argument is not iterable."""
    fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
    filing_22en: xf.Filing = upm23en_filing # Right operand
    method_callable = getattr(fs_21_22, method)
    # Call fs_21_22.<method>(filing_22en)
    assert method_callable(filing_22en) is NotImplemented


##### Test simple methods #####


def test_copy(upm21to22_filingset):
    """Test shallow copy method."""
    fs: xf.FilingSet = upm21to22_filingset
    filings = set(fs)
    entities = {f.entity for f in fs}
    fs_copy = fs.copy()

    assert isinstance(fs_copy, xf.FilingSet)
    assert fs_copy is not fs, 'Different FilingSet identity'
    assert filings == set(fs_copy), 'Same Filing identities in new FilingSet'
    entities_copy = {f.entity for f in fs_copy}
    assert entities == entities_copy, 'Same Entity identity in new FilingSet'


class TestAdd:
    """Test add method."""

    def test_new_type(
            self, upm21to22_filingset, upm23en_filing):
        """Test type remains when adding new."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        fs_result.add(filing_23en)
        assert isinstance(fs_result, xf.FilingSet)

    def test_new_filing_count(
            self, upm21to22_filingset, upm23en_filing):
        """Test FilingSet item count when adding new."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        fs_result.add(filing_23en)
        msg = (
            '{21en, 21fi, 22en, 22fi}.add(23en) '
            '== {21en, 21fi, 22en, 22fi, 23en}, got len() == '
            f'{len(fs_result)}'
            )
        assert len(fs_result) == 5, msg

    def test_new_filing_api_id(
            self, upm21to22_filingset, upm23en_filing):
        """Test Filing api_id values when adding new."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        fs_result.add(filing_23en)

        e_ids = {
            ID_UPM21_EN, ID_UPM21_FI, ID_UPM22_EN, ID_UPM22_FI, ID_UPM23_EN}
        ids_result = {f.api_id for f in fs_result}
        assert ids_result == e_ids, 'Filing api_id values match expected'

    def test_new_filing_deepcopy_or_retain(
            self, upm21to22_filingset, upm23en_filing):
        """Test Filing deepcopied (new item) or retained when adding new."""
        fs_21_22: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        fs_result = xf.FilingSet(fs_21_22)
        fs_result.add(filing_23en)

        fil = _build_ref_dict([(fs_result, 'result'), (fs_21_22, '21_22')])
        assert fil['21en_result'] is fil['21en_21_22'], 'Filing 21en retained from left'
        assert fil['21fi_result'] is fil['21fi_21_22'], 'Filing 21fi retained from left'
        assert fil['22en_result'] is fil['22en_21_22'], 'Filing 22en retained from left'
        assert fil['22fi_result'] is fil['22fi_21_22'], 'Filing 22fi retained from left'
        assert fil['23en_result'] is not filing_23en, 'Filing 23en (deep)copied'

    def test_new_entity_filings_count(
            self, upm21to22_filingset, upm23en_filing):
        """Test Entity.filings item count when adding new."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        fs_result.add(filing_23en)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        assert len(ent_result.filings) == 5, (
            'As many backreferences as filings')

    def test_new_entity_filings_api_id(
            self, upm21to22_filingset, upm23en_filing):
        """Test Entity.filings api_id are the same as for FilingSet."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        fs_result.add(filing_23en)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        e_ids = {
            ID_UPM21_EN, ID_UPM21_FI, ID_UPM22_EN, ID_UPM22_FI, ID_UPM23_EN}
        fil_ids_backref = {f.api_id for f in ent_result.filings}
        assert fil_ids_backref == e_ids, (
            'Entity.filings api_id values as expected')

    def test_existing_type(self, upm21to22_filingset, upm22en_filing):
        """Test type remains when adding existing."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        fs_result.add(filing_22en)
        assert isinstance(fs_result, xf.FilingSet)

    def test_existing_filing_count(self, upm21to22_filingset, upm22en_filing):
        """Test FilingSet item count when adding existing."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        fs_result.add(filing_22en)
        msg = (
            '{21en, 21fi, 22en, 22fi}.add(22en) '
            '== {21en, 21fi, 22en, 22fi}, got len() == '
            f'{len(fs_result)}'
            )
        assert len(fs_result) == 4, msg

    def test_existing_api_id(self, upm21to22_filingset, upm22en_filing):
        """Test Filing api_id values when adding existing."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        fs_result.add(filing_22en)
        e_ids = {ID_UPM21_EN, ID_UPM21_FI, ID_UPM22_EN, ID_UPM22_FI}
        ids_result = {f.api_id for f in fs_result}
        assert ids_result == e_ids, 'Filing api_id values match expected'

    def test_existing_filing_retained(
            self, upm21to22_filingset, upm22en_filing):
        """Test Filing retained when adding existing."""
        fs_21_22: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        fs_result = xf.FilingSet(fs_21_22)
        fs_result.add(filing_22en)
        fil = _build_ref_dict([(fs_result, 'result'), (fs_21_22, '21_22')])
        assert fil['21en_result'] is fil['21en_21_22'], 'Filing 21en retained from left'
        assert fil['21fi_result'] is fil['21fi_21_22'], 'Filing 21fi retained from left'
        assert fil['22en_result'] is fil['22en_21_22'], 'Filing 22en retained from left'
        assert fil['22fi_result'] is fil['22fi_21_22'], 'Filing 22fi retained from left'

    def test_wrong_type_raises(self, upm21to22_filingset, upm23en_filing):
        """Test adding Entity to FilingSet raises."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        ent_23en: xf.Entity = filing_23en.entity
        with pytest.raises(
                TypeError, match=r'FilingSet can only contain Filing objects'):
            fs_result.add(ent_23en)
        assert isinstance(fs_result, xf.FilingSet)
        assert len(fs_result) == 4


class TestRemoveDiscard:
    """Test remove/discard method."""

    @pytest.mark.parametrize('method', ['remove', 'discard'])
    def test_success_type(
            self, method, upm21to22_filingset, upm22en_filing):
        """Test type remains when successful."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        _execute_operation(method, fs_result, filing_22en)
        assert isinstance(fs_result, xf.FilingSet)

    @pytest.mark.parametrize('method', ['remove', 'discard'])
    def test_success_filing_count(
            self, method, upm21to22_filingset, upm22en_filing):
        """Test FilingSet item count when successful."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        _execute_operation(method, fs_result, filing_22en)
        msg = (
        '{21en, 21fi, 22en, 22fi}'
        f'.{method}(22en) '
        '== {21en, 21fi, 22fi}, got len() == '
        f'{len(fs_result)}'
        )
        assert len(fs_result) == 3, msg

    @pytest.mark.parametrize('method', ['remove', 'discard'])
    def test_success_filing_api_id(
            self, method, upm21to22_filingset, upm22en_filing):
        """Test Filing api_id values when successful."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        _execute_operation(method, fs_result, filing_22en)
        e_ids = {ID_UPM21_EN, ID_UPM21_FI, ID_UPM22_FI}
        ids_result = {f.api_id for f in fs_result}
        assert ids_result == e_ids, 'Filing api_id values match expected'

    @pytest.mark.parametrize('method', ['remove', 'discard'])
    def test_success_filing_deepcopy_or_retain(
            self, method, upm21to22_filingset, upm22en_filing):
        """Test Filing deepcopied (new item) or retained when adding new."""
        fs_21_22: xf.FilingSet = upm21to22_filingset
        filing_22en: xf.Filing = upm22en_filing
        fs_result = xf.FilingSet(fs_21_22)
        _execute_operation(method, fs_result, filing_22en)

        fil = _build_ref_dict([(fs_result, 'result'), (fs_21_22, '21_22')])
        assert fil['21en_result'] is fil['21en_21_22'], 'Filing 21en retained from left'
        assert fil['21fi_result'] is fil['21fi_21_22'], 'Filing 21fi retained from left'
        assert fil['22fi_result'] is fil['22fi_21_22'], 'Filing 22fi retained from left'

    def test_missing_remove(self, upm21to22_filingset, upm23en_filing):
        """Test remove method by removing an item not present."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23en: xf.Filing = upm23en_filing
        with pytest.raises(KeyError, match=re.escape(repr(filing_23en))):
            fs_result.remove(filing_23en)
        assert isinstance(fs_result, xf.FilingSet)
        assert len(fs_result) == 4

    def test_missing_discard(self, upm21to22_filingset, upm23en_filing):
        """Test discard method by removing an item not present."""
        fs_result: xf.FilingSet = upm21to22_filingset
        filing_23: xf.Filing = upm23en_filing
        fs_result.discard(filing_23)
        assert isinstance(fs_result, xf.FilingSet)
        assert len(fs_result) == 4


def test_pop(upm21to22_filingset):
    """Test pop method."""
    fs_result: xf.FilingSet = upm21to22_filingset
    filing = fs_result.pop()

    assert isinstance(fs_result, xf.FilingSet)
    assert isinstance(filing, xf.Filing)
    assert len(fs_result) == 3

    ent_result: xf.Entity = next(iter(fs_result.entities))
    assert len(ent_result.filings) == 3


##### Test subresource coherence #####
# I.e. Entity and ValidationMessage counts and cross-references


@pytest.mark.parametrize('method', [
    *BASIC_SET_OPERATION_METHODS, *SIMPLE_METHODS])
class TestEntity:
    """Test Entity."""

    def test_entity_count(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity count as separate identities from Filing to Entity references."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        right_operand: Union[xf.FilingSet, xf.Filing] = _get_right_operand(
            method, upm22to23_filingset)
        fs_result = _execute_operation(method, fs_21_22, right_operand)
        ents_result = {f.entity for f in fs_result}
        assert len(ents_result) == 1, 'Same entity for all filings'

    def test_entity_identity(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity identity."""
        isedit = method in BASIC_SET_OPERATION_EDIT_METHODS
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        right_operand: Union[xf.FilingSet, xf.Filing] = _get_right_operand(
            method, upm22to23_filingset)
        fs_result = _execute_operation(method, fs_21_22, right_operand)
        ent_result: xf.Entity = next(iter(fs_result.entities))
        ent_21_22 = next(iter(fs_21_22.entities))

        # Entity of left operand
        if isedit:
            assert ent_result is ent_21_22, 'Entity retained from left side'
        else:
            assert ent_result is not ent_21_22, 'Entity (deep)copied'

        # Entity of right operand
        if isinstance(right_operand, xf.FilingSet):
            ent_22_23 = next(iter(right_operand.entities))
            msg = (
                'Entity rejected from left side' if isedit
                else 'Entity (deep)copied'
                )
            assert ent_result is not ent_22_23, msg
        elif isinstance(right_operand, xf.Filing):
            assert ent_result is not right_operand.entity, 'Entity (deep)copied'

    def test_entity_filings_identity(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test Entity.filings to Filing backreference identity."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        right_operand: Union[xf.FilingSet, xf.Filing] = _get_right_operand(
            method, upm22to23_filingset)
        fs_result = _execute_operation(method, fs_21_22, right_operand)
        ent_result: xf.Entity = next(iter(fs_result.entities))

        fil = _build_ref_dict([
            (fs_result, 'result'), (ent_result.filings, 'backref')])
        msg = (
            'Backreference for {} in Entity.filings is not the same as '
            'FilingSet item'
            )
        if fil['21en_result']:
            assert fil['21en_result'] is fil['21en_backref'], msg.format('21en')
        if fil['21fi_result']:
            assert fil['21fi_result'] is fil['21fi_backref'], msg.format('21fi')
        if fil['22en_result']:
            assert fil['22en_result'] is fil['22en_backref'], msg.format('22en')
        if fil['22fi_result']:
            assert fil['22fi_result'] is fil['22fi_backref'], msg.format('22fi')
        if fil['23en_result']:
            assert fil['23en_result'] is fil['23en_backref'], msg.format('23en')
        if fil['23fi_result']:
            assert fil['23fi_result'] is fil['23fi_backref'], msg.format('23fi')


@pytest.mark.parametrize('method', [
    *BASIC_SET_OPERATION_METHODS, *SIMPLE_METHODS])
class TestValidationMessage:
    """Test ValidationMessage."""

    def _assert_refs(
            self, filing_result: xf.Filing, filing_orig: xf.Filing,
            issame: bool):
        for vmsg_result in filing_result.validation_messages:
            match_id = vmsg_result.api_id
            vmsg_orig = next(
                v for v in filing_orig.validation_messages
                if v.api_id == match_id
                )
            if issame:
                assert vmsg_orig is vmsg_result, (
                    'ValidationMessage is retained from left')
            else:
                assert vmsg_orig is not vmsg_result, (
                    'ValidationMessage is (deep)copied')
            vmsg_dups = [
                v for v in filing_result.validation_messages
                if v.api_id == match_id
                ]
            assert len(vmsg_dups) == 1, (
                'Only unique ValidationMessage.api_id values in results')

    def test_validationmessage_filing_identity(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test ValidationMessage.filing backreference identity."""
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        right_operand: Union[xf.FilingSet, xf.Filing] = _get_right_operand(
            method, upm22to23_filingset)
        fs_result = _execute_operation(method, fs_21_22, right_operand)

        filing_ref_msg = (
            'ValidationMessage.filing cross-references '
            'Filing.validation_messages'
            )
        for filing_result in fs_result:
            # ValidationMessage to Filing leads to original Filing
            for vmsg in filing_result.validation_messages:
                assert vmsg.filing is filing_result, filing_ref_msg

    def test_deepcopy_or_retain(
            self, method, upm21to22_filingset, upm22to23_filingset):
        """Test ValidationMessage is retained (isedit=True, left) or deepcopied."""
        isedit = method in BASIC_SET_OPERATION_EDIT_METHODS
        fs_21_22: xf.FilingSet = upm21to22_filingset # Left operand
        right_operand: Union[xf.FilingSet, xf.Filing] = _get_right_operand(
            method, upm22to23_filingset)
        fs_result = _execute_operation(method, fs_21_22, right_operand)

        # Filing.validation_messages are deepcopied for right set.
        # Deepcopied for left if new set operation otherwise retained.
        for filing_result in fs_result:
            match_id = filing_result.api_id
            filing_left = next(
                (f for f in fs_21_22 if f.api_id == match_id), None)
            filing_right = None
            if isinstance(right_operand, xf.FilingSet):
                filing_right = next(
                    (f for f in right_operand if f.api_id == match_id), None)
            if (isinstance(right_operand, xf.Filing)
                    and right_operand.api_id == match_id):
                filing_right = right_operand

            if filing_left and not filing_right:
                # Left only filing
                if isedit:
                    self._assert_refs(filing_result, filing_left, issame=True)
                else:
                    self._assert_refs(filing_result, filing_left, issame=False)
            elif filing_left:
                # Shared filing
                if isedit:
                    self._assert_refs(filing_result, filing_left, issame=True)
                else:
                    self._assert_refs(filing_result, filing_left, issame=False)
                self._assert_refs(filing_result, filing_right, issame=False)
            else:
                # Right only filings
                self._assert_refs(filing_result, filing_left, issame=False)
