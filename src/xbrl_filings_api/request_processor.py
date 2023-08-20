"""
Module for processing API requests.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Mapping, Sequence, Iterable, Generator
from datetime import date, datetime, timedelta, UTC
import itertools
import urllib.parse

import requests

from .api_object.api_error import APIErrorGroup, APIError
from .api_object.entity import Entity
from .api_object.filing import Filing
from .api_object.filings_page import FilingsPage
from .api_object.validation_message import ValidationMessage
from .api_request import APIRequest
from .enums import (
    ScopeFlag, GET_ONLY_FILINGS, GET_ENTITY, GET_VALIDATION_MESSAGES, NO_LIMIT)
from .exceptions import HTTPStatusError
from .filing_set.resource_collection import ResourceCollection
import xbrl_filings_api.options as options

page_counter = 0
api_attribute_map: dict[str, str]


def generate_pages(
        filters: Mapping[str, str | Iterable[str]] | None,
        sort: Sequence[str] | None,
        max_size: int,
        flags: ScopeFlag,
        add_api_params: Mapping | None,
        res_colls: dict[str, ResourceCollection]
        ) -> Generator[FilingsPage, None, None]:
    """
    Generate instances of `FilingsPage` from the API.

    Parameters
    ----------
    filters : mapping of str: {str, iterable of str}, optional
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
    APIErrorGroup of APIError
    HTTPStatusError
    requests.ConnectionError
    requests.JSONDecodeError

    Warns
    -----
    ApiIdCoherenceWarning
    ApiReferenceWarning
    """
    params = {}
    received_api_ids: dict[str, set] = dict()

    page_size = options.max_page_size
    # NO_LIMIT is int(0)
    if max_size < NO_LIMIT:
        page_size = max_size
    elif max_size > NO_LIMIT:
        if max_size < page_size:
            page_size = max_size
    params['page[size]'] = page_size

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
    
    request_param_list = _get_request_param_list(filters, params)

    request_time = _get_request_time()
    
    received_size = 0
    for params in request_param_list:
        next_url = options.entry_point_url
        while next_url:
            page_json, api_request = _retrieve_page_json(
                next_url, params, request_time)
            
            page = FilingsPage(
                page_json, api_request, flags, received_api_ids, res_colls)
            if len(page.filing_list) == 0:
                break
            next_url = page.api_next_page_url
                
            received_size += len(page.filing_list)
            if received_size > max_size:
                page.filing_list = page.filing_list[:max_size - received_size]

            yield page

            if not next_url or received_size >= max_size:
                break
            params = None
        if received_size >= max_size:
            break


def _get_request_param_list(
        filters: Mapping[str, str | Iterable[str]] | None,
        params: dict[str, str]
        ) -> list[dict[str, str] | None]:
    if not filters:
        return [params]

    date_filters = {
        fld: filters[fld] for fld in filters if fld.endswith('_date')}
    for fld in date_filters:
        del filters[fld]
    
    multifilters = {
        fld: filters[fld] for fld in filters
        if isinstance(filters[fld], Iterable)
        and not isinstance(filters[fld], str)
        }
    for fld in multifilters:
        del filters[fld]

    if date_filters:
        year_filter_months = options.year_filter_months
        if year_filter_months[1] <= year_filter_months[0]:
            msg = (
                'The option year_filter_months stop (2nd item) is before '
                'or equal to start (1st item)'
                )
            raise ValueError(msg)

        for field_name, filter_iterb in date_filters.items():
            if isinstance(filter_iterb, str):
                filter_iterb = [filter_iterb]
            resolved = []
            for date_filter in filter_iterb:
                nums = [int(num) for num in date_filter.split('-')]
                if len(nums) == 1:
                    year = nums[0]
                    start_part, stop_part = year_filter_months
                    req_year, req_month = year+start_part[0], start_part[1]
                    stop_year, stop_month = year+stop_part[0], stop_part[1]

                    mf_values = []
                    while (req_year, req_month) < (stop_year, stop_month):
                        month_end = _get_month_end(req_year, req_month)
                        mf_values.append(month_end.strftime('%Y-%m-%d'))

                        req_month += 1
                        if req_month > 12:
                            req_year, req_month = req_year+1, 1
                    resolved.append(mf_values)

                if len(nums) == 2:
                    year, month = nums
                    month_end = _get_month_end(year, month)
                    resolved.append(month_end.strftime('%Y-%m-%d'))
                else:
                    resolved.append(date_filter)
            if len(resolved) == 1:
                filters[field_name] = resolved[0]
            else:
                multifilters[field_name] = resolved
    
    params |= _filters_to_query_params(filters)

    if not multifilters:
        return [params]
    else:
        # Cartesian product of multifilter values
        filters_add_list = [
            dict(zip(multifilters.keys(), values))
            for values in itertools.product(*multifilters.values())
            ]
        rp_list = []
        for filters_add in filters_add_list:
            req_params = params.copy()
            req_params |= _filters_to_query_params(filters_add)
            rp_list.append(req_params)
        return rp_list


def _get_month_end(year: int, month: int) -> date:
    next_month = date(year, month, 28) + timedelta(days=4)
    last_day = next_month - timedelta(days=next_month.day)
    return last_day


def _filters_to_query_params(filters: dict[str, str]) -> dict[str, str]:
    global api_attribute_map
    qparams = dict()
    for field_name, value in filters.items():
        try:
            field_name = api_attribute_map[field_name]
        except KeyError:
            pass
        qparams[f'filter[{field_name}]'] = value
    return qparams


def _get_sort_query_param(sort: Sequence[str]) -> str:
    global api_attribute_map
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


def _get_request_time() -> datetime:
    request_time = datetime.now()
    if options.utc_time:
        request_time = request_time.astimezone(UTC)
    else:
        request_time = request_time.astimezone()
    return request_time


def _retrieve_page_json(
        url: str, params: dict | None, request_time: datetime
        ) -> tuple[dict, APIRequest]:
    """
    Execute an API request and return the deserialized JSON object.
    
    Raises
    ------
    APIErrorGroup of APIError
    HTTPStatusError
    requests.ConnectionError
    """
    global page_counter
    
    furl = url
    if params and len(params) > 0:
        furl += '?' + '&'.join([f'{key}={val}' for key, val in params.items()])
    print(f'GET {urllib.parse.unquote(furl)}')

    res = requests.get(
        url, params, headers={'Content-Type': 'application/vnd.api+json'})
    page_counter += 1
    api_request = APIRequest(res.url, request_time)

    if res.status_code == 200:
        print('  > Success')
    else:
        print('  > STATUS ' + str(res.status_code))

    json_frag = res.json()
    if json_frag.get('errors'):
        msg = (
            f'The filings API returned errors. Status {res.status_code} '
            + res.reason
            )
        excs = [
            APIError(
                err_frag, url, api_request, res.status_code, res.reason)
            for err_frag in json_frag['errors']
            ]
        raise APIErrorGroup(msg, excs)
    elif res.status_code != 200:
        raise HTTPStatusError(res.status_code, res.reason, res.text)

    return json_frag, api_request


def get_api_attribute_map() -> dict[str, str]:
    attrmap = dict()
    for proto in (Filing(...), Entity(...), ValidationMessage(...)):
        cls = proto.__class__
        for prop in dir(proto):
            if getattr(cls, prop, False):
                continue
            api_attr = getattr(cls, prop.upper(), False)
            if api_attr and api_attr.startswith('attributes.'):
                attr_lib = prop
                attr_api = api_attr[11:]
                if cls.TYPE != 'filing':
                    attr_lib = f'{cls.TYPE}.{attr_lib}'
                    attr_api = f'{cls.TYPE}.{attr_api}'
                attrmap[attr_lib] = attr_api
    return attrmap


api_attribute_map = get_api_attribute_map()
