"""Define general tests for package."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import inspect
from datetime import datetime
from types import FunctionType

import pytest

import xbrl_filings_api as xf
from xbrl_filings_api.api_request import _APIRequest


def test_all_public_classes_have_repr():
    """Test that all concrete root module classes have custom __repr__."""
    pclasses = [
        getattr(xf, name)
        for name in dir(xf)
        if inspect.isclass(getattr(xf, name))
        ]
    for pclass in pclasses:
        if (issubclass(pclass, Exception)
                and not issubclass(pclass, xf.APIObject)):
            continue
        cname = pclass.__name__
        # Skip non-concrete classes
        if cname in ('APIObject', 'APIResource'):
            continue
        crepr = getattr(pclass, '__repr__', False)
        msg = f'{pclass} must have custom __repr__'
        assert isinstance(crepr, FunctionType), msg


def test_nonconcrete_classes_init_fails():
    """Test non-concrete classes cannot be initialized."""
    with pytest.raises(NotImplementedError):
        xf.APIObject(json_frag={}, api_request=_APIRequest('', datetime.now()))
    with pytest.raises(NotImplementedError):
        xf.APIResource(json_frag={})
