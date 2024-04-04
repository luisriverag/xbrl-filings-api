"""Define general tests for package."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import dataclasses
import inspect
import pkgutil
import textwrap
from collections.abc import Callable
from pathlib import Path
from types import FunctionType, ModuleType
from typing import Union

import pytest

import xbrl_filings_api as xf

TESTS_PATH = Path(__file__).parent.parent


def _get_package_callables_recursively(
        pkg: ModuleType,
        pkg_import_name: Union[str, None] = None,
        pkg_callables: Union[tuple[list[str], list[Callable]], None] = None
        ) -> tuple[list[str], list[Callable]]:
    if not pkg_import_name:
        pkg_import_name = pkg.__name__
    if not pkg_callables:
        pkg_callables = [], []

    mod_iter = pkgutil.iter_modules(pkg.__path__)
    for _, mod_name, ispkg in mod_iter:
        if mod_name.startswith('__'):
            continue
        import_name = f'{pkg_import_name}.{mod_name}'

        # Import package/module
        o_name = pkgutil.resolve_name(import_name)

        if ispkg:
            _get_package_callables_recursively(
                o_name, import_name, pkg_callables)
            continue
        for attr_name in dir(o_name):
            if attr_name.startswith('__'):
                continue
            attr_val = getattr(o_name, attr_name)
            if not callable(attr_val):
                continue
            _append_callables_recursively(pkg_callables, attr_val, import_name, import_name)
    return pkg_callables


def _append_callables_recursively(
        pkg_callables: tuple[list[str], list[Callable]],
        cur_call: Callable,
        pkg_import_name: str,
        cls_access_path: str
        ) -> None:
    if getattr(cur_call, '__module__', None) != pkg_import_name:
        return
    if cur_call in pkg_callables[1]:
        return
    access_path = f'{cls_access_path}.{cur_call.__name__}'
    pkg_callables[0].append(access_path)
    pkg_callables[1].append(cur_call)
    if inspect.isclass(cur_call) and not dataclasses.is_dataclass(cur_call):
        for class_attr in dir(cur_call):
            if class_attr not in cur_call.__dict__:
                # Inherited methods have access_path of their own class
                continue
            attr_val = getattr(cur_call, class_attr)
            if callable(attr_val):
                _append_callables_recursively(
                    pkg_callables, attr_val, pkg_import_name, access_path)


def _build_callable_duplicate_string(
        c_names: list[str], c_objs: list[Callable]) -> Union[str, None]:
    c_count = len(c_names)
    doc_to_names: dict[int, list[str]] = {}
    for c_idx in range(c_count):
        cname = c_names[c_idx]
        cobj = c_objs[c_idx]
        doc = cobj.__doc__
        if doc:
            if doc not in doc_to_names:
                doc_to_names[doc] = []
            doc_to_names[doc].append(cname)
    multidoc_to_names: dict[int, list[str]] = {}
    for doc, names in doc_to_names.items():
        if len(names) > 1:
            multidoc_to_names[doc] = names
    if multidoc_to_names:
        jnames = ''
        indent = ' '*4
        for doc, names in multidoc_to_names.items():
            jnames += (
                f'\n"{textwrap.shorten(doc, width=67)}"\n{indent}'
                + f'\n{indent}'.join(sorted(names))
                )
        msg = (
            'The following callable(s) have duplicate docstrings:\n'
            + jnames
            )
        return msg
    return None


def test_all_public_classes_have_repr():
    """
    Test that all concrete root module classes have custom __repr__.
    """
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


def test_nonconcrete_classes_init_fails(dummy_api_request):
    """Test non-concrete classes cannot be initialized."""
    with pytest.raises(NotImplementedError):
        xf.APIObject(json_frag={}, api_request=dummy_api_request)
    with pytest.raises(NotImplementedError):
        xf.APIResource(json_frag={})


pytest.mark.skip(reason='Not yet checked out')
def test_all_callables_have_unique_docstrings():
    """
    Test that all callables have unique docstrings in package and
    subpackage(s).
    """
    c_names, c_objs = _get_package_callables_recursively(xf)
    msg = _build_callable_duplicate_string(c_names, c_objs)
    if msg:
        pytest.fail(reason=msg)


pytest.mark.skip(reason='Not yet checked out')
def test_all_tests_have_unique_docstrings(all_test_functions):
    """
    Test that all tests have unique docstrings.

    This test cannot be run in isolation. It requires all tests to be
    collected.
    """
    c_objs = []
    c_names = []
    for fname, func in all_test_functions.items():
        c_objs.append(func)
        c_names.append(fname)
    msg = _build_callable_duplicate_string(c_names, c_objs)
    if msg:
        pytest.fail(reason=msg)
