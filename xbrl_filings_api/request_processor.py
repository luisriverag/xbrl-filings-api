"""Module for processing API requests."""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import itertools
import urllib.parse
from collections.abc import Generator, Iterable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Literal

import requests

import xbrl_filings_api.options as options
import xbrl_filings_api.stats as stats
from xbrl_filings_api.api_object import (
    APIError,
    APIErrorGroup,
    Entity,
    Filing,
    FilingsPage,
    ValidationMessage,
)
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.enums import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    NO_LIMIT,
    ScopeFlag,
)
from xbrl_filings_api.exceptions import HTTPStatusError
from xbrl_filings_api.filing_set.resource_collection import ResourceCollection

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
    params: dict[str, str] = {}
    received_api_ids: dict[str, set] = {}

    page_size = options.max_page_size
    # NO_LIMIT is int(0)
    if max_size < NO_LIMIT:
        page_size = max_size
    elif max_size > NO_LIMIT:
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

    request_param_list = _get_request_param_list(filters, params)

    request_time = _get_request_time()

    received_size = 0
    for req_params in request_param_list:
        next_url: str | None = options.entry_point_url
        while next_url:
            page_json, api_request = _retrieve_page_json(
                next_url, req_params, request_time)

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
            req_params = None
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
    working_filters = {
        fld: filters[fld] for fld in filters if fld not in date_filters}

    multifilters = {
        fld: working_filters[fld] for fld in working_filters
        if isinstance(working_filters[fld], Iterable)
        and not isinstance(working_filters[fld], str)
        }
    for fld in multifilters:
        del working_filters[fld]

    if date_filters:
        if options.year_filter_months[1] <= options.year_filter_months[0]:
            msg = (
                'The option year_filter_months stop (2nd item) is before '
                'or equal to start (1st item)'
                )
            raise ValueError(msg)

        for field_name, filter_iterb in date_filters.items():
            if isinstance(filter_iterb, str):
                filter_iterb = [filter_iterb]
            resolved: list[str] = []
            for date_filter in filter_iterb:
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
                working_filters[field_name] = resolved[0]
            else:
                multifilters[field_name] = resolved

    # working_filters values are all non-iterables
    params |= _filters_to_query_params(working_filters) # type: ignore

    if not multifilters:
        return [params]
    else:
        # Cartesian product of multifilter values
        filters_add_list = [
            dict(zip(multifilters.keys(), values))
            for values in itertools.product(*multifilters.values())
            ]
        rp_list: list[dict[str, str] | None] = []
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
    global api_attribute_map  # noqa: PLW0602
    qparams = {}
    for field_name, value in filters.items():
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


def _get_request_time() -> datetime:
    tz = UTC if options.utc_time else None
    request_time = datetime.now(tz)
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
    furl = url
    if params and len(params) > 0:
        furl += '?' + '&'.join([f'{key}={val}' for key, val in params.items()])
    print(f'GET {urllib.parse.unquote(furl)}')

    res = requests.get(
        url, params, headers={'Content-Type': 'application/vnd.api+json'},
        timeout=options.timeout_sec
        )
    stats.page_counter += 1
    api_request = APIRequest(res.url, request_time)

    if res.status_code == 200:  # noqa: PLR2004
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
                err_frag, api_request, res.status_code, res.reason)
            for err_frag in json_frag['errors']
            ]
        raise APIErrorGroup(msg, excs)
    elif res.status_code != 200:  # noqa: PLR2004
        raise HTTPStatusError(res.status_code, res.reason, res.text)

    return json_frag, api_request


def _get_api_attribute_map() -> dict[str, str]:
    attrmap = {}
    for proto in (Filing(...), Entity(...), ValidationMessage(...)):
        cls = proto.__class__
        for prop in dir(proto):
            if getattr(cls, prop, False):
                continue
            api_attr: str | Literal[False] = (
                getattr(cls, prop.upper(), False)) # type: ignore
            if api_attr and api_attr.startswith('attributes.'):
                attr_lib = prop
                attr_api = api_attr[11:]
                if cls.TYPE != 'filing':
                    attr_lib = f'{cls.TYPE}.{attr_lib}'
                    attr_api = f'{cls.TYPE}.{attr_api}'
                attrmap[attr_lib] = attr_api
    return attrmap


api_attribute_map = _get_api_attribute_map()
