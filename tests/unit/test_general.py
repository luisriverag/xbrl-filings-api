"""Define general tests for package."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import inspect
from types import FunctionType

import xbrl_filings_api as xf


def test_all_public_classes_have_repr():
    """Test that all concrete root module classes have custom __repr__."""
    pclasses = [
        getattr(xf, name)
        for name in dir(xf)
        if inspect.isclass(getattr(xf, name))
        ]
    for pclass in pclasses:
        cname = pclass.__name__
        # Skip non-concrete classes
        if cname in ('APIObject', 'APIResource'):
            continue
        crepr = getattr(pclass, '__repr__', False)
        assert isinstance(crepr, FunctionType), f'{cname} must have repr'
