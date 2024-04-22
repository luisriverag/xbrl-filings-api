"""Define function `order_columns`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable

__all__ = ['order_columns']


def order_columns(cols: Iterable[str]) -> list[str]:
    """
    Order column names for display.

    1. ``api_id``
    2. *<all the rest>*
    3. Ends with ``_count`` (`Filing` class)
    4. Starts with ``calc_`` and ends ``_sum`` (`ValidationMessage`
       class)
    5. Starts with ``calc_`` (``ValidationMessage`` class)
    6. Starts with ``duplicate_`` (``ValidationMessage`` class)
    7. Ends with ``_time``
    8. Ends with ``_api_id``
    9. Ends with ``_url``
    10. Ends with ``_path`` (``Filing`` class)
    11. Ends with ``_sha256`` (``Filing`` class)
    12. Ends with ``query_time``
    13. Ends with ``request_url``
    """
    col_tuples = []
    for col in cols:
        order = 1
        if col == 'api_id':
            order = 0
        elif col.endswith('_time'):
            order = 10
        elif col.endswith('_api_id'):
            order = 20
        elif col.endswith('_url'):
            order = 22
        if col == 'query_time':
            order = 40
        if col == 'request_url':
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
