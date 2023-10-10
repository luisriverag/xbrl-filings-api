"""Module for processing API requests."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import itertools
import logging
import urllib.parse
from collections.abc import Generator, Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal, Union

import requests

from xbrl_filings_api import options, stats
from xbrl_filings_api.api_error import APIError
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.constants import NO_LIMIT
from xbrl_filings_api.enums import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    ScopeFlag,
)
from xbrl_filings_api.exceptions import HTTPStatusError
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.filings_page import FilingsPage
from xbrl_filings_api.order_columns import order_columns
from xbrl_filings_api.resource_collection import ResourceCollection

UTC = timezone.utc
logger = logging.getLogger(__name__)

api_attribute_map: dict[str, str]


def generate_pages(
        filters: Union[Mapping[str, Union[Any, Iterable[Any]]], None],
        sort: Union[Sequence[str], None],
        max_size: int,
        flags: ScopeFlag,
        add_api_params: Union[Mapping, None],
        res_colls: dict[str, ResourceCollection]
        ) -> Generator[FilingsPage, None, None]:
    """
    Generate instances of `FilingsPage` from the API.

    Parameters
    ----------
    filters : mapping of str: {any, iterable of any}, optional
    sort: sequence of str or None
    max_size : int or NO_LIMIT
    flags : ScopeFlag
    add_api_params : mapping, optional
    res_colls : dict of str: ResourceCollection

    Yields
    ------
    FilingsPage
        New page object from API.

    Raises
    ------
    APIError
    HTTPStatusError
    requests.ConnectionError
    requests.JSONDecodeError
    """
    params: dict[str, str] = {}
    received_api_ids: dict[str, set] = {}

    page_size = options.max_page_size
    # NO_LIMIT is int(0)
    if max_size < 0:
        msg = 'Parameter "max_size" may not be negative'
        raise ValueError(msg)
    elif max_size > 0:
        if max_size < page_size:
            page_size = max_size
    params['page[size]'] = str(page_size)

    include_flags = []
    if GET_ONLY_FILINGS not in flags:
        if GET_ENTITY in flags:
            include_flags.append('entity')
        if GET_VALIDATION_MESSAGES in flags:
            include_flags.append('validation_messages')
    if len(include_flags) > 0:
        params['include'] = ','.join(include_flags)

    if sort:
        params['sort'] = _get_sort_query_param(sort)
    if add_api_params:
        params.update(add_api_params)

    params_list = _get_params_list_on_filters(params, filters)

    query_time = _get_query_time()

    received_size = 0
    for query_params in params_list:
        next_url: Union[str, None] = options.entry_point_url
        req_params: Union[dict[str, str], None] = query_params
        while next_url:
            page_json, api_request = _retrieve_page_json(
                next_url, req_params, query_time)

            page = FilingsPage(
                page_json, api_request, flags, received_api_ids, res_colls)
            filing_count = len(page.filing_list)
            if filing_count == 0:
                break
            next_url = page.api_next_page_url

            received_size += filing_count
            if max_size != NO_LIMIT and received_size > max_size:
                del_count = received_size - max_size
                _remove_excess_resources(page, del_count)

            yield page

            if not next_url or received_size >= max_size:
                # Query exhausted
                break
            req_params = None

        if max_size != NO_LIMIT and received_size >= max_size:
            # Limit of `max_size` is exhausted before full multiquery/
            # short date query
            break


def _remove_excess_resources(page: FilingsPage, del_count: int):
    """Delete api resources beyond `max_size` on last page."""
    for filing in page.filing_list[-del_count:]:
        if filing.entity and page.entity_list:
            filing.entity.filings.remove(filing)
            if len(filing.entity.filings) == 0:
                page.entity_list.remove(filing.entity)
        if filing.validation_messages and page.validation_message_list:
            for vmessage in filing.validation_messages:
                page.validation_message_list.remove(vmessage)
    page.filing_list = page.filing_list[:-del_count]


def _get_params_list_on_filters(
        params: dict[str, str],
        filters: Union[Mapping[str, Union[Any, Iterable[Any]]], None]
        ) -> list[dict[str, str]]:
    """Append filter keys to `params` dict."""
    if not filters:
        return [params]

    date_filters: dict[str, list[str]] = {}
    for fld, val in filters.items():
        if fld.endswith('_date'):
            # Turn literal into a list of a string
            if (not isinstance(val, Iterable)
                    or isinstance(val, str)):
                date_filters[fld] = [str(val)]
            # Normalize iterables into lists of strings
            else:
                date_filters[fld] = [str(item) for item in val]

    multifilters: dict[str, list[str]] = {}
    for fld, iterb in filters.items():
        if (fld not in date_filters
            and isinstance(iterb, Iterable)
            and not isinstance(iterb, str)):
            # Normalize multifilter values to list of strings
            multifilters[fld] = [str(val) for val in iterb]

    # Normalise single filters into strings
    single_filters: dict[str, str] = {
        fld: str(val)
        for fld, val in filters.items()
        if fld not in date_filters
        and fld not in multifilters
        }

    if date_filters:
        _resolve_date_filters(date_filters, multifilters, single_filters)

    params |= _filters_to_query_params(single_filters)

    if multifilters:
        return _expand_params_on_multifilters(params, multifilters)
    else:
        return [params]


def _resolve_date_filters(
        date_filters: dict[str, list[str]],
        multifilters: dict[str, list[str]],
        single_filters: dict[str, str]
        ) -> None:
    """Resolve `date_filters` into filter dicts."""
    if options.year_filter_months[1] <= options.year_filter_months[0]:
        msg = (
            'The option year_filter_months stop (2nd item) is before '
            'or equal to start (1st item)'
            )
        raise ValueError(msg)

    for field_name, filter_list in date_filters.items():
        resolved: list[str] = []
        for date_filter in filter_list:
            nums = [int(num) for num in date_filter.split('-')]

            if len(nums) == 1:
                year = nums[0]
                start_part, stop_part = options.year_filter_months
                req_year, req_month = year+start_part[0], start_part[1]
                stop_year, stop_month = year+stop_part[0], stop_part[1]

                mf_values = []
                while (req_year, req_month) < (stop_year, stop_month):
                    month_end = _get_month_end(req_year, req_month)
                    mf_values.append(month_end.strftime('%Y-%m-%d'))

                    req_month += 1
                    if req_month > 12:  # noqa: PLR2004
                        req_year, req_month = req_year+1, 1
                resolved.extend(mf_values)

            if len(nums) == 2:  # noqa: PLR2004
                year, month = nums
                month_end = _get_month_end(year, month)
                resolved.append(month_end.strftime('%Y-%m-%d'))
            else:
                resolved.append(date_filter)
        if len(resolved) == 1:
            single_filters[field_name] = resolved[0]
        else:
            multifilters[field_name] = resolved


def _expand_params_on_multifilters(
        params: dict[str, str],
        multifilters: dict[str, list[str]]
        ) -> list[dict[str, str]]:
    """
    Return lists of request params based on expanded multifilters.

    A Cartesian product will be taked from multifilters and these sets
    of filters will be appended to the list of static params to form
    complete param sets for multiple API requests.
    """
    params_append_list = [
        dict(zip(multifilters.keys(), values))
        for values in itertools.product(*multifilters.values())
        ]
    rp_list = []
    for params_append in params_append_list:
        req_params = params.copy()
        req_params |= _filters_to_query_params(params_append)
        rp_list.append(req_params)
    return rp_list


def _get_month_end(year: int, month: int) -> date:
    next_month = date(year, month, 28) + timedelta(days=4)
    last_day = next_month - timedelta(days=next_month.day)
    return last_day


def _filters_to_query_params(
        single_filters: dict[str, str]
        ) -> dict[str, str]:
    global api_attribute_map  # noqa: PLW0602
    qparams = {}
    for field_name, value in single_filters.items():
        try:
            filter_name = api_attribute_map[field_name]
        except KeyError:
            qparams[f'filter[{field_name}]'] = value
        else:
            qparams[f'filter[{filter_name}]'] = value
    return qparams


def _get_sort_query_param(sort: Sequence[str]) -> str:
    global api_attribute_map  # noqa: PLW0602
    qparam = ''
    for field in sort:
        if qparam != '':
            qparam += ','
        field_name = field[1:] if field.startswith('-') else field
        try:
            field_name = api_attribute_map[field_name]
        except KeyError:
            pass
        if field.startswith('-'):
            qparam += '-'
        qparam += field_name
    return qparam


def _get_query_time() -> datetime:
    tz = UTC if options.utc_time else None
    query_time = datetime.now(tz)
    return query_time


def _retrieve_page_json(
        url: str, params: Union[dict, None], query_time: datetime
        ) -> tuple[dict, _APIRequest]:
    """
    Execute an API request and return the deserialized JSON object.

    Raises
    ------
    APIError
    HTTPStatusError
    requests.ConnectionError
    """
    req_i = stats.page_counter + 1
    furl = url
    if params and len(params) > 0:
        furl += '?' + '&'.join([f'{key}={val}' for key, val in params.items()])
    furl = urllib.parse.unquote(furl)
    logger.info(f'GET Req#{req_i} {furl}')

    res = requests.get(
        url, params, headers={'Content-Type': 'application/vnd.api+json'},
        timeout=options.timeout_sec
        )
    stats.page_counter = req_i
    api_request = _APIRequest(res.url, query_time)

    if res.status_code == 200:  # noqa: PLR2004
        logger.info(f'Success for Req#{req_i}')
    else:
        logger.error(
            f'Error with Req#{req_i}, status {res.status_code} {res.reason}')

    json_frag = res.json()
    if json_frag.get('errors'):
        err_frag: Union[dict, None] = next(iter(json_frag['errors']), None)
        if err_frag:
            raise APIError(err_frag, api_request, res.status_code, res.reason)
    elif res.status_code != 200:  # noqa: PLR2004
        raise HTTPStatusError(res.status_code, res.reason, res.text)

    return json_frag, api_request


def _get_api_attribute_map() -> dict[str, str]:
    attrmap: dict[str, str] = {}
    fproto = Filing(...)
    cls = fproto.__class__
    clsmap = {'api_id': 'id'}
    for prop in dir(fproto):
        # Exclude class attributes from instance attributes
        if getattr(cls, prop, False):
            continue

        api_attr: Union[str, Literal[False]] = (
            getattr(cls, prop.upper(), False)) # type: ignore
        if api_attr and api_attr.startswith('attributes.'):
            attr_lib = prop
            attr_api = api_attr[11:]
            clsmap[attr_lib] = attr_api
    ordcols = order_columns(clsmap.keys())
    ordered_clsmap = {
        lib_attr: clsmap[lib_attr]
        for lib_attr in ordcols
        }
    attrmap |= ordered_clsmap
    return attrmap


api_attribute_map = _get_api_attribute_map()
"""
Mapping from library attribute names to JSON:API used names.

Is used to convert fields in `sort` and `filters` parameters of queries.
"""

FILING_QUERY_ATTRS = list(api_attribute_map)
"""
List of resource attribute names for `sort` and `filter` parameters.

Does not include derived attributes. Despite capital letter naming, this
value is derived from the library, but as per general API maintenance
principles, this list is expected only to grow.
"""
