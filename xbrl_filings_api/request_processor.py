"""
Module for processing API requests.

Despite being an internal module, `FILING_QUERY_ATTRS` will be
accessible from package root.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import itertools
import logging
import urllib.parse
import warnings
from collections.abc import Generator, Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta, timezone
from json import JSONDecodeError
from typing import Any, Literal, Union

import requests

from xbrl_filings_api import options, stats
from xbrl_filings_api.api_error import APIError
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.constants import NO_LIMIT, PROTOTYPE
from xbrl_filings_api.exceptions import (
    FilterNotSupportedWarning,
    HTTPStatusError,
    JSONAPIFormatError,
)
from xbrl_filings_api.filing import Filing
from xbrl_filings_api.filings_page import FilingsPage
from xbrl_filings_api.order_columns import order_columns
from xbrl_filings_api.resource_collection import ResourceCollection
from xbrl_filings_api.scope_flag import ScopeFlag

__all__ = [
    'generate_pages',
    'api_attribute_map',
    'FILING_QUERY_ATTRS',
    ]

UTC = timezone.utc
logger = logging.getLogger(__name__)

api_attribute_map: dict[str, str]

_ParamsType = dict[str, Union[str, int]]


def generate_pages(
        filters: Union[Mapping[str, Union[Any, Iterable[Any]]], None],
        limit: int,
        flags: ScopeFlag,
        res_colls: dict[str, ResourceCollection],
        sort: Union[str, Sequence[str], None] = None,
        add_api_params: Union[Mapping, None] = None,
        ) -> Generator[FilingsPage, None, None]:
    """
    Generate instances of `FilingsPage` from the API.

    Parameters
    ----------
    filters : mapping of {str: any or iterable of any}, optional
    limit : int or NO_LIMIT
    flags : ScopeFlag
    res_colls : dict of {str: ResourceCollection}
    sort: sequence of str, optional
    add_api_params : mapping, optional

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
    if isinstance(sort, str):
        sort = [sort]

    params: _ParamsType = {}
    received_api_ids: dict[str, set] = {}

    page_size = options.max_page_size
    # NO_LIMIT is int(0)
    if limit < 0:
        msg = 'Parameter "limit" may not be negative'
        raise ValueError(msg)
    elif limit > 0:
        if limit < page_size:
            page_size = limit
    params['page[size]'] = page_size

    stats.query_call_counter += 1
    logger.info(
        f'Query call #{stats.query_call_counter} started | {filters=}, '
        f'{sort=}, {limit=}, {flags=}, {add_api_params=}'
        )

    include_flags = []
    if ScopeFlag.GET_ONLY_FILINGS not in flags:
        if ScopeFlag.GET_ENTITY in flags:
            include_flags.append('entity')
        if ScopeFlag.GET_VALIDATION_MESSAGES in flags:
            include_flags.append('validation_messages')
    if len(include_flags) > 0:
        params['include'] = ','.join(include_flags)

    if sort:
        params['sort'] = _get_sort_query_param(sort)
    if add_api_params:
        params.update(add_api_params)

    aq_1st_num = stats.api_query_counter + 1
    params_list = _get_params_list_on_filters(params, filters, aq_1st_num)
    params_list_len = len(params_list)

    query_time = datetime.now(UTC)

    # For each separate simple query
    # Multifilters and short dates cause multiple simple queries
    received_size = 0
    for qparam_i, query_params in enumerate(params_list):
        next_url: Union[str, None] = options.entry_point_url
        req_params: Union[_ParamsType, None] = query_params
        aq_num = aq_1st_num + qparam_i
        stats.api_query_counter = aq_num

        # For each page in the query
        while next_url:
            page_json, api_request = _retrieve_page_json(
                next_url, req_params, query_time, aq_num)
            stats.page_counter += 1

            page = FilingsPage(
                page_json, api_request, flags, received_api_ids, res_colls)
            filing_count = len(page.filing_list)
            if filing_count == 0:
                break
            next_url = page.api_next_page_url

            # Last page on paged query typically has more results
            # than the query `limit`
            received_size += filing_count
            if limit != NO_LIMIT and received_size > limit:
                del_count = received_size - limit
                _remove_excess_resources(page, del_count)

            yield page

            if limit != NO_LIMIT and received_size >= limit:
                # Query `limit` reached
                break
            req_params = None

        if limit != NO_LIMIT and received_size >= limit:
            # `limit` is exhausted before full multiquery/short date
            # query
            break

        if limit != NO_LIMIT:
            # Lower requested count of filings for further requests
            for update_i in range(qparam_i + 1, params_list_len):
                pdict = params_list[update_i]
                # Type of page[size] is always int
                pdict['page[size]'] -= filing_count # type: ignore[operator]


def _remove_excess_resources(page: FilingsPage, del_count: int):
    """Delete api resources beyond parameter `limit` on last page."""
    for filing in page.filing_list[-del_count:]:
        if filing.entity and page.entity_list:
            filing.entity.filings.remove(filing)
            if len(filing.entity.filings) == 0:
                page.entity_list.remove(filing.entity)
        if filing.validation_messages and page.validation_message_list:
            for vmessage in filing.validation_messages:
                page.validation_message_list.remove(vmessage)
    page.filing_list = page.filing_list[:-del_count]


def _raise_for_none_filters(
        filters: Mapping[str, Union[Any, Iterable[Any]]]):
    nonemsg = 'Value None is not allowed for filters, field "{}"{}'
    for fld, val in filters.items():
        if isinstance(val, Iterable) and not isinstance(val, str):
            # Multifilter
            for multifilter_i, single_filter in enumerate(val):
                if single_filter is None:
                    msg = nonemsg.format(fld, _get_mf_index_str(multifilter_i))
                    raise ValueError(msg)
        elif val is None:
            # Single filter
            msg = nonemsg.format(fld, '')
            raise ValueError(msg)


def _get_params_list_on_filters(
        params: _ParamsType,
        filters: Union[Mapping[str, Union[Any, Iterable[Any]]], None],
        aq_1st_num: int
        ) -> list[_ParamsType]:
    """Append filter keys to `params` dict."""
    if not filters:
        return [params]
    _raise_for_none_filters(filters)

    # Filters differentiated by their type from field name ending
    # fgroup[group_name][field_name] = [str_value1, str_value2, ...]
    fgroup: dict[str, dict[str, list[str]]] = {}

    # Function calls change `fgroup`, classify to
    # 'other', 'date' or 'time'
    for field_name, filter_value in filters.items():
        _classify_normalize_filter(fgroup, field_name, filter_value)

    _expand_short_date_filters(fgroup)

    # Extract single filters from `fgroup`
    single_filters: dict[str, str] = {}
    fgroup_del: dict[str, list[str]] = {}
    for group_name in fgroup:
        for field_name, val_list in fgroup[group_name].items():
            if len(val_list) == 1:
                single_filters[field_name] = val_list[0]
                if group_name not in fgroup_del:
                    fgroup_del[group_name] = []
                fgroup_del[group_name].append(field_name)

    # Exclude single filters from `fgroup` leaving only multifilters
    for group_name in fgroup_del:
        for field_name in fgroup_del[group_name]:
            del fgroup[group_name][field_name]
            if len(fgroup[group_name]) == 0:
                del fgroup[group_name]

    params |= _filters_to_query_params(single_filters)

    # If there are multifilters left in `fgroup`, expand them to
    # multiple groups of parameters for many queries
    if fgroup:
        params_lists = _expand_params_on_multifilters(params, fgroup)
        for pset_i, pset in enumerate(params_lists):
            pset_num = aq_1st_num + pset_i
            logger.info(f'API query #{pset_num} parameter set: {pset}')
        return params_lists
    else:
        logger.info(f'Parameter set: {params}')
        return [params]


def _filters_to_query_params(
        single_filters: dict[str, str]
        ) -> dict[str, str]:
    global api_attribute_map  # noqa: PLW0602
    qparams = {}
    for field_name, value in single_filters.items():
        try:
            supported_name = api_attribute_map[field_name]
        except KeyError:
            msg = (
                f'Field name "{field_name}" is not supported but can be used '
                'to filter'
                )
            warnings.warn(msg, FilterNotSupportedWarning, stacklevel=1)
            qparams[f'filter[{field_name}]'] = value
        else:
            qparams[f'filter[{supported_name}]'] = value
    return qparams


def _classify_normalize_filter(
        fgroup: dict[str, dict[str, list[str]]], field_name: str,
        filter_value: object) -> None:
    """Classify a filter, normalize and process it as strings."""
    group_name = 'other'
    if field_name.endswith('_date'):
        group_name = 'date'
    if field_name.endswith('_time'):
        group_name = 'time'

    vlist: list[str] = []
    if (isinstance(filter_value, Iterable)
        and not isinstance(filter_value, str)):
        # Multifilter value
        for multifilter_i, single_filter in enumerate(filter_value):
            processed = _process_single_filter_value(
                field_name, single_filter, group_name, multifilter_i)
            vlist.append(processed)
    else:
        # Single filter value
        processed = _process_single_filter_value(
            field_name, filter_value, group_name, None)
        vlist.append(processed)

    if group_name not in fgroup:
        fgroup[group_name] = {}
    fgroup[group_name][field_name] = vlist


def _process_single_filter_value(
        field_name: str, val: object, group_name: str,
        multifilter_i: Union[int, None]
        ) -> str:
    """Process non-iterable filter value according to type."""
    if group_name == 'date':
        return _process_date_filter(field_name, val, multifilter_i)
    if group_name == 'time':
        return _process_time_filter(field_name, val, multifilter_i)
    else:
        return str(val)


def _process_date_filter(
        field_name: str, val: object, multifilter_i: Union[int, None]
        ) -> str:
    """Raise for datetime value, convert to string."""
    if isinstance(val, datetime):
        msg = (
            f'Not possible to filter date field "{field_name}" by datetime'
            + _get_mf_index_str(multifilter_i)
            )
        raise ValueError(msg)
    processed_val = str(val)
    return processed_val


def _process_time_filter(
        field_name: str, val: object, multifilter_i: Union[int, None]
        ) -> str:
    """Raise for bad time filter and convert string to UTC timezone."""
    if isinstance(val, date) and not isinstance(val, datetime):
        # Value is a simple date object without time information
        msg = (
            f'Not possible to filter datetime field "{field_name}" by date'
            + _get_mf_index_str(multifilter_i)
            )
        raise ValueError(msg)

    proc_dt: datetime
    if isinstance(val, datetime):
        if val.tzinfo is None:
            proc_dt = val.replace(tzinfo=UTC)
        else:
            proc_dt = val.astimezone(UTC)
    else:
        val_str = str(val)
        for try_i in range(2):
            parsed_dt: Union[datetime, None] = None
            try:
                if try_i == 0:
                    parsed_dt = datetime.fromisoformat(val_str)
                else:
                    # For Python 3.10 and earlier in case timezones
                    # are taken to use in API datetime strings
                    parsed_dt = datetime.strptime(
                        val_str, '%Y-%m-%d %H:%M:%S.%f%z')
            except ValueError:
                pass
            if isinstance(parsed_dt, datetime):
                proc_dt = parsed_dt
                break
        else:
            msg = (
                'Not possible to parse datetime in filter field '
                f'"{field_name}" string "{val_str}"'
                + _get_mf_index_str(multifilter_i)
                )
            raise ValueError(msg)
    fmt = '%Y-%m-%d %H:%M:%S'
    if proc_dt.microsecond > 0:
        fmt += '.%f'
    return proc_dt.strftime(fmt)


def _get_mf_index_str(multifilter_i: Union[int, None]) -> str:
    """Get multifilter index string for ValueError."""
    if multifilter_i is None:
        return ''
    else:
        return f', multifilter index {multifilter_i}'


def _expand_short_date_filters(
        fgroup: dict[str, dict[str, list[str]]]
        ) -> None:
    """Expand year-only and year-month-only dates as multifilters."""
    if 'date' not in fgroup:
        return

    if options.year_filter_months[1] <= options.year_filter_months[0]:
        msg = (
            'The option year_filter_months stop (2nd item) is before '
            'or equal to start (1st item)'
            )
        raise ValueError(msg)

    for rname, r_i in [('start', 0), ('stop', 1)]:
        # 12 months is no magic (PLR2004)
        if not (1 <= options.year_filter_months[r_i][1] <= 12): # noqa: PLR2004
            msg = (
                f'options.year_filter_months {rname} month definition must be '
                'in 1..12'
                )
            raise ValueError(msg)

    for field_name, date_list in fgroup['date'].items():
        resolved: list[str] = []
        for pos, date_filter in enumerate(date_list):
            nums = [int(num) for num in date_filter.split('-')]
            if len(nums) > 3: # noqa: PLR2004
                multifilter_i = pos if len(date_list) > 1 else None
                msg = (
                    f'Date in filter field "{field_name}" is not a valid date '
                    f'or short date, value: "{date_filter}"'
                    + _get_mf_index_str(multifilter_i)
                    )
                raise ValueError(msg)

            # Short date for (financial) year expanded according to
            # month closings in `options.year_filter_months`
            if len(nums) == 1:
                year = nums[0]
                start_part, stop_part = options.year_filter_months
                req_year, req_month = year+start_part[0], start_part[1]
                stop_year, stop_month = year+stop_part[0], stop_part[1]

                month_closings = []
                while (req_year, req_month) < (stop_year, stop_month):
                    month_end = _get_month_end(req_year, req_month)
                    month_closings.append(month_end.strftime('%Y-%m-%d'))

                    req_month += 1
                    if req_month > 12:  # noqa: PLR2004
                        req_year, req_month = req_year+1, 1
                resolved.extend(month_closings)

            # Short date for month closing
            elif len(nums) == 2:  # noqa: PLR2004
                year, month = nums
                month_end = _get_month_end(year, month)
                resolved.append(month_end.strftime('%Y-%m-%d'))
            else:
                resolved.append(date_filter)
        fgroup['date'][field_name] = resolved


def _expand_params_on_multifilters(
        params: _ParamsType,
        fgroup: dict[str, dict[str, list[str]]]
        ) -> list[_ParamsType]:
    """
    Return lists of request params based on expanded multifilters.

    A Cartesian product will be taked from multifilters and these sets
    of filters will be appended to the list of static params to form
    complete param sets for multiple API requests.
    """
    multifilters: dict[str, list[str]] = {}
    if 'other' in fgroup:
        multifilters |= fgroup['other']
    if 'time' in fgroup:
        multifilters |= fgroup['time']
    if 'date' in fgroup:
        multifilters |= fgroup['date']

    params_append_list = [
        dict(zip(multifilters.keys(), values))
        for values in itertools.product(*multifilters.values())
        ]
    request_param_list: list[_ParamsType] = []
    for params_append in params_append_list:
        req_params = params.copy()
        req_params |= _filters_to_query_params(params_append)
        request_param_list.append(req_params)
    return request_param_list


def _get_month_end(year: int, month: int) -> date:
    next_month = date(year, month, 28) + timedelta(days=4)
    last_day = next_month - timedelta(days=next_month.day)
    return last_day


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


def _retrieve_page_json(
        url: str, params: Union[_ParamsType, None],
        query_time: datetime, aq_num: int
        ) -> tuple[dict, APIRequest]:
    """
    Execute an API request and return the deserialized JSON object.

    Raises
    ------
    APIError
    HTTPStatusError
    requests.ConnectionError
    """
    furl = url
    if params and len(params) > 0:
        furl += '?' + '&'.join([f'{key}={val}' for key, val in params.items()])
    furl = urllib.parse.unquote(furl)
    logger.info(f'GET request #{aq_num} {furl}')

    res = requests.get(
        url, params, headers={'Content-Type': 'application/vnd.api+json'},
        timeout=options.timeout_sec
        )
    api_request = APIRequest(res.url, query_time)

    if res.status_code == 200:  # noqa: PLR2004
        logger.info(f'Success for page of API query #{aq_num}')
    else:
        logger.error(
            f'Error with page request for API query #{aq_num}, '
            f'status {res.status_code} {res.reason}'
            )
        # HTTPStatusError is raised later

    json_frag = decode_error = None
    try:
        json_frag = res.json()
    except JSONDecodeError as err:
        decode_error = err

    if (isinstance(json_frag, dict)
            and json_frag.get('errors')
            and isinstance(json_frag['errors'], list)):
        err_frag: Any = next(iter(json_frag['errors']), None)
        if err_frag and isinstance(err_frag, dict):
            raise APIError(err_frag, api_request, res.status_code, res.reason)
    elif res.status_code != 200:  # noqa: PLR2004
        raise HTTPStatusError(res.status_code, res.reason, res.text)
    elif decode_error:
        raise decode_error
    elif not isinstance(json_frag, dict):
        msg = 'JSON:API document is not a JSON object'
        raise JSONAPIFormatError(msg)
    elif json_frag.get('data') is None and json_frag.get('meta') is None:
        msg = (
            'JSON:API document does not have any of the required keys '
            '"data", "errors", "meta".'
            )
        raise JSONAPIFormatError(msg)

    return json_frag, api_request


def _get_api_attribute_map() -> dict[str, str]:
    attrmap: dict[str, str] = {}
    fproto = Filing(PROTOTYPE)
    clsmap = {'api_id': 'id'}
    for prop in dir(fproto):
        # Exclude class attributes from instance attributes
        if getattr(Filing, prop, False):
            continue

        # All Filing instance attribute names as upper case are JSON
        # paths as strings if originating from the response
        api_attr: Union[str, Literal[False]] = (
            getattr(Filing, prop.upper(), False)) # type: ignore[assignment]

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
r"""
Mapping from library attribute names to names used in the API.

Is used to convert fields in parameters ``sort`` and ``filters``.
"""

FILING_QUERY_ATTRS = list(api_attribute_map)
"""
List of resource attribute names for parameters ``sort`` and ``filter``.

Does not include derived attributes. Despite capital letter naming, this
value is derived from the library, but as per general API maintenance
principles, this list is expected only to grow.
"""
