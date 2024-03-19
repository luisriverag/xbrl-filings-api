"""Define tests for `APIResource`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import datetime

import pytest

import xbrl_filings_api as xf
from xbrl_filings_api.api_request import _APIRequest


def test_raises_APIResource_init():
    """Test raising for direct APIResource __init__."""
    with pytest.raises(NotImplementedError):
        xf.APIResource(json_frag={})


def test_raises_APIResource_get_data_attributes():
    """Test raising for APIResource.get_data_attributes."""
    with pytest.raises(NotImplementedError):
        xf.APIResource.get_data_attributes(flags=None, filings=None)


def test_Filing_get_data_attributes():
    """Test Filing.get_data_attributes, flags=None."""
    dattrs = xf.Filing.get_data_attributes(flags=None, filings=None)
    for dattr in dattrs:
        assert isinstance(dattr, str)
    assert 'entity_api_id' not in dattrs


def test_Filing_get_data_attributes_GET_ONLY_FILINGS():
    """Test Filing.get_data_attributes, flags=GET_ONLY_FILINGS."""
    dattrs = xf.Filing.get_data_attributes(flags=xf.GET_ONLY_FILINGS, filings=None)
    assert 'entity_api_id' not in dattrs


def test_Filing_get_data_attributes_GET_ENTITY():
    """Test Filing.get_data_attributes, flags=GET_ENTITY."""
    dattrs = xf.Filing.get_data_attributes(flags=xf.GET_ENTITY, filings=None)
    assert 'entity_api_id' in dattrs


def test_raises_APIResource_get_columns():
    """Test raising for APIResource.get_columns."""
    with pytest.raises(NotImplementedError):
        xf.APIResource.get_columns(filings=None, has_entities=False)
