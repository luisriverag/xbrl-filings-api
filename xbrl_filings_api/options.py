"""
General options for the library.

Globals
-------
entry_point_url : str, default 'https://filings.xbrl.org/api/filings'
    URL entry point to be used for the API.
max_page_size : int, default 200
    Defines the maximum number of main resources (typically
    filings) to be retrieved in a single request. If the functions
    are called by limiting the number of results with a
    parameter `max_size` which is smaller than this value, page
    size will be set as `max_size` instead.
time_accuracy : {'day', 'min', 'sec', 'max'}, default 'min'
    The smallest time unit to be shown when converting times to
    strings. This includes database values. Option ``day`` shows
    only dates and ``max`` fractional seconds.
year_filter_months : YearFilterMonthsType, default ((0, 8), (1, 8))
    Range of months to request when `filters` has a date
    field with only year defined. First int of inner tuples is a
    year offset and the second is the month of the year. Range
    end is non-inclusive, so default means until July.
views : Set of SQLiteView, default DEFAULT_VIEWS
    Set of `SQLiteView` objects. The `name` attributes of objects may
    not be overlapping.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Set
from typing import Union

from xbrl_filings_api.constants import YearFilterMonthsType
from xbrl_filings_api.default_views import DEFAULT_VIEWS
from xbrl_filings_api.sqlite_view import SQLiteView

entry_point_url: str = 'https://filings.xbrl.org/api/filings'
"""JSON-API entry point URL."""

max_page_size: int = 200
"""Maximum batch of main resources to be fetched on a single page."""

time_accuracy: str = 'min'
"""String conversion of datetimes which must be a key of
`time_formats.time_formats`.
"""

year_filter_months: YearFilterMonthsType = ((0, 8), (1, 8))
"""
Define queried months when parameter `filters` includes a date-type
field which is being filtered solely by year.

Two values of tuple are start and stop where start is inclusive and stop
is exclusive. Inner tuples have two values where the first is year
offset and the second is calendar-style month number (e.g. 8 is August).
"""

views: Union[Set[SQLiteView], None] = DEFAULT_VIEWS
"""
SQLite3 views to be added to created databases.

The `name` attributes of objects may not be overlapping. `SQLiteView`
objects use `name` for hashing, so adding another view with the same
name to the set will be discarded.
"""

timeout_sec: float = 30.0
"""Maximum number of seconds to wait for response from the server."""
