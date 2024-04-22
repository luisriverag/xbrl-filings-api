"""General options for the library."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
import webbrowser
from collections.abc import Iterable
from typing import Union

from xbrl_filings_api.constants import YearFilterMonthsType
from xbrl_filings_api.default_views import DEFAULT_VIEWS
from xbrl_filings_api.sqlite_view import SQLiteView

__all__ = [
    'browser',
    'entry_point_url',
    'max_page_size',
    'open_viewer',
    'timeout_sec',
    'views',
    'year_filter_months',
    ]

logger = logging.getLogger(__name__)


browser: Union[webbrowser.BaseBrowser, None] = None
"""
The web browser controller object used for `Filing.open()` method.

If value is :pt:`None`, it will be set when ``Filing.open()`` is
called. Valid value can be created with :func:`webbrowser.get` function.

Default value is :pt:`None`.
"""

entry_point_url: str = 'https://filings.xbrl.org/api/filings'
"""
API entry point URL for requests.

Default value is ``'https://filings.xbrl.org/api/filings'``.
"""

max_page_size: int = 200
"""
Maximum number of main resources to be fetched on a single page.

Defines the maximum number of filings to be retrieved in a single API
response. If the functions are called by limiting the number of results
with a parameter ``limit`` which is smaller than this value, page size
will be set as ``limit`` instead.

Default value is ``200``.
"""

open_viewer: bool = True
"""
Open viewer instead of plain XHTML file on `Filing.open()` call.

Default value is :pt:`True`.
"""

timeout_sec: float = 30.0
"""
Maximum number of seconds to wait for response from the server.

Default value is ``30.0``.
"""

views: Union[Iterable[SQLiteView], None] = DEFAULT_VIEWS
"""
SQLite3 views to be added to created/edited databases.

The `SQLiteView.name` attributes of objects may not be overlapping.

Default value is `DEFAULT_VIEWS`.
"""

year_filter_months: YearFilterMonthsType = ((0, 8), (1, 8))
"""
Define queried months when filtering a date field by only a year.

Two values of tuple are start and stop where start is inclusive and stop
is exclusive. Inner tuples have two values where the first is year
offset and the second is calendar-style month number (e.g. 8 is August).

Default value is :pt:`((0, 8), (1, 8))` which means from August in
specified year until July in following year.
"""
