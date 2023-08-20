"""
Data utility functions for the library.

Used for data output.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable

from ..constants import ATTRS_ALWAYS_EXCLUDE_FROM_DATA
from ..enums import ScopeFlag, GET_ONLY_FILINGS, GET_ENTITY


def get_data_attributes(
        resource_type: type[object], flags: ScopeFlag | None = None,
        filings: Iterable[object] | None = None
        ) -> list[str]:
    """
    Get data attributes for `resource_type`.

    Excludes internal and class attributes and the ones containing
    objects.

    For `Filing` objects this also means excluding attributes ending
    ``_download_path`` if all filings have this column filled with
    `None`. Additionally, if `GET_ENTITY` is not set filings will
    exclude `entity_api_id`.

    Parameters
    ----------
    resource_type : type of APIResource
        The requested resource type.
    flags : ScopeFlag, optional
        Only relevant for `Filing` resource type.
    filings : iterable of Filing, optional
        Only relevant for `Filing` resource type.
    """
    resource_proto = resource_type(...)
    attrs = [
        attr for attr in dir(resource_proto)
        if not (
            attr.startswith('_')
            or getattr(resource_type, attr, False)
            or attr in ATTRS_ALWAYS_EXCLUDE_FROM_DATA)
        ]
    if resource_type.TYPE == 'filing':
        if filings:
            exclude_dlpaths = (
                _get_unused_download_paths(resource_type, filings))
            attrs = [attr for attr in attrs if attr not in exclude_dlpaths]
        if GET_ENTITY not in flags:
            attrs.remove('entity_api_id')
    return order_columns(attrs)


def _get_unused_download_paths(
        resource_type: type[object], filings: Iterable[object]) -> set[str]:
    """
    Get unused `Filing` object attributes ending in ``_download_path``.

    Parameters
    ----------
    resource_type : type[Filing]
    filings : iterable of Filing
    """
    fproto = resource_type(...)
    dlattrs = [
        att for att in dir(fproto)
        if not att.startswith('_') and att.endswith('_download_path')
        ]
    
    unused = set()
    for att in dlattrs:
        for fil in filings:
            if getattr(fil, att) is not None:
                break
        else:
            unused.add(att)
    return unused


def order_columns(cols: list[str]) -> list[str]:
    col_tuples = []
    for col in cols:
        order = 1
        if col == 'api_id':
            order = 0
        elif col.endswith('_time'):
            order = 10
        elif col.endswith('_api_id'):
            order = 20
        elif col in ATTRS_ALWAYS_EXCLUDE_FROM_DATA:
            order = 21
        elif col.endswith('_url'):
            order = 22
        if col.endswith('request_time'):
            order = 40
        if col.endswith('request_url'):
            order = 41
        
        # Filing objects
        if col.endswith('_count'):
            order = 2
        elif col.endswith('_path'):
            order = 30
        elif col.endswith('_sha256'):
            order = 31
        
        # ValidationMessage objects
        if col.startswith('calc_'):
            if col.endswith('_sum'):
                order = 2
            else:
                order = 3
        elif col.startswith('duplicate_'):
            order = 4
        
        col_tuples.append((order, col))
    col_tuples.sort()
    return [col for order, col in col_tuples]


def get_columns(
        resource_type: type[object], has_entities: bool = False,
        filings: Iterable[object] | None = None
        ) -> list[str]:
    """
    List of available columns for this set.

    Parameters
    ----------
    resource_type : type of APIResource
        Resource type for which the columns are fetched.
    has_entities : bool, default False
        Only relevant for `Filing` objects.
    filings: iterable of Filing, optional
        Only relevant for `Filing` objects.
    """
    flags = GET_ONLY_FILINGS
    if has_entities:
        flags = GET_ENTITY
    cols = get_data_attributes(resource_type, flags, filings)
    return order_columns(cols)
