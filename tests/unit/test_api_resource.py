"""Define tests for `APIResource`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api as xf
from xbrl_filings_api.constants import _PROTOTYPE


def test_raises_APIResource_init():
    """Test raising for direct APIResource __init__."""
    with pytest.raises(NotImplementedError):
        xf.APIResource(json_frag={})


def test_raises_Filing_init_without_api_request():
    """Test raising for Filing init without api_request."""
    with pytest.raises(ValueError, match=r'Parameter api_request not given'):
        xf.Filing(json_frag={})


def test_raises_Filing_init_prototype():
    """Test initiating Filing prototype with `_PROTOTYPE` argument."""
    fproto = xf.Filing(_PROTOTYPE)
    assert fproto.api_id == 'None'


def test_raises_APIResource_get_data_attributes():
    """Test raising for APIResource.get_data_attributes."""
    with pytest.raises(NotImplementedError):
        xf.APIResource.get_data_attributes(flags=None, filings=None)


def test_Filing_get_data_attributes_sanity_check():
    """Test Filing.get_data_attributes, flags=None."""
    dattrs = xf.Filing.get_data_attributes(flags=None, filings=None)
    for dattr in dattrs:
        assert isinstance(dattr, str)
    assert 'api_id' in dattrs
    assert 'filing_index' in dattrs
    assert 'entity_api_id' not in dattrs


def test_Filing_get_data_attributes_GET_ONLY_FILINGS():
    """Test Filing.get_data_attributes, flags=GET_ONLY_FILINGS."""
    dattrs = xf.Filing.get_data_attributes(
        flags=xf.GET_ONLY_FILINGS, filings=None)
    assert 'entity_api_id' not in dattrs


def test_Filing_get_data_attributes_GET_ENTITY():
    """Test Filing.get_data_attributes, flags=GET_ENTITY."""
    dattrs = xf.Filing.get_data_attributes(flags=xf.GET_ENTITY, filings=None)
    assert 'entity_api_id' in dattrs


def test_Filing_get_data_attributes_filings_no_paths(get_oldest3_fi_filingset):
    """Test Filing.get_data_attributes with a FilingSet, no paths."""
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    dattrs = xf.Filing.get_data_attributes(flags=None, filings=fs)
    for dattr in dattrs:
        assert not dattr.endswith('_download_path')


def test_Filing_get_data_attributes_filings_xhtml_path(
        get_oldest3_fi_filingset):
    """
    Test Filing.get_data_attributes with a FilingSet, has
    xhtml_download_path.
    """
    fs: xf.FilingSet = get_oldest3_fi_filingset()
    fsiter = iter(fs)
    next(fsiter)
    f2 = next(fsiter)
    f2.xhtml_download_path = 'test'

    dattrs = xf.Filing.get_data_attributes(flags=None, filings=fs)
    assert 'xhtml_download_path' in dattrs
    dattrs.remove('xhtml_download_path')
    for dattr in dattrs:
        assert not dattr.endswith('_download_path')


def test_ValidationMessage_get_data_attributes_sanity_check():
    """Test ValidationMessage.get_data_attributes."""
    dattrs = xf.ValidationMessage.get_data_attributes(flags=None, filings=None)
    for dattr in dattrs:
        assert isinstance(dattr, str)
    assert 'api_id' in dattrs
    assert 'code' in dattrs
    assert 'filing_api_id' in dattrs


def test_Entity_get_data_attributes_sanity_check():
    """Test Entity.get_data_attributes."""
    dattrs = xf.Entity.get_data_attributes(flags=None, filings=None)
    for dattr in dattrs:
        assert isinstance(dattr, str)
    assert 'api_id' in dattrs
    assert 'name' in dattrs


def test_raises_APIResource_get_columns():
    """Test raising for APIResource.get_columns."""
    with pytest.raises(NotImplementedError):
        xf.APIResource.get_columns(filings=None, has_entities=False)


def test_Filing_get_columns_sanity_check():
    """Test Filing.get_columns, has_entities=False."""
    dattrs = xf.Filing.get_columns(filings=None, has_entities=False)
    for dattr in dattrs:
        assert isinstance(dattr, str)
    assert 'api_id' in dattrs
    assert 'filing_index' in dattrs
    assert 'entity_api_id' not in dattrs


def test_Filing_get_columns_has_entities_true():
    """Test Filing.get_columns, has_entities=True."""
    dattrs = xf.Filing.get_columns(filings=None, has_entities=True)
    assert 'entity_api_id' in dattrs
