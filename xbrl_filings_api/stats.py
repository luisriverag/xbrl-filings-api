"""Module for API stats counters."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

query_call_counter = 0
"""
Count of query calls started since the library was first imported.

This is the number of calls to methods such as
`xbrl_filings_api.get_filings` or `xbrl_filings_api.to_sqlite`. A query
call consists of one or more API queries (multiple in case of
multifilters) which in turn consist of pages.
"""

api_query_counter = 0
"""
Count of API queries started since the library was first imported.

An API query is a set of URL parameters used to demand certain kind of
content from the API. A call to method such as
`xbrl_filings_api.get_filings` may consist of multiple API queries in
case of multifilter values or short dates. An API query consists of one
or more pages.
"""

page_counter = 0
"""
Count of pages received since the library was first imported.

A page is a received HTTP response. A single API query may consist of
multiple pages.
"""
