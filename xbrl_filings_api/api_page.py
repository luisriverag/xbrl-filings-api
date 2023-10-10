"""Define `_APIPage` and `_IncludedResource` classes."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import urllib
from dataclasses import dataclass
from typing import Union

from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.enums import _ParseType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _IncludedResource:
    type_: str
    id_: str
    frag: dict


class _APIPage(APIObject):
    """
    Base class for JSON:API response page or document.

    Attributes
    ----------
    api_self_url : str or None
    api_prev_page_url : str or None
    api_next_page_url : str or None
    api_first_page_url : str or None
    api_last_page_url : str or None
    jsonapi_version : str or None
    query_time : datetime
    request_url : str
    """

    def __init__(self, json_frag: dict, api_request: _APIRequest):
        super().__init__(json_frag, api_request)

        self._data: Union[list, None] = self._json.get(
            'data')
        """List of main resources as unserialized JSON fragments of the
        page.
        """

        self._included_resources: list[_IncludedResource] = (
            self._get_included_resources())
        """
        List of included resources as objects with fields `type_`, `id_`
        and `frag`.

        This list should be emptied and classified to class-specific
        attributes for sets of objects in the subclass `__init__`
        methods.
        """

        self._data_count: Union[int, None] = self._json.get(
            'meta.count')
        """Total count of total main resources of the query including
        the ones not on this page.
        """

        self.api_self_url: Union[str, None] = self._json.get(
            'links.self', _ParseType.URL)
        """Link to this JSON:API page."""

        self.api_prev_page_url: Union[str, None] = self._json.get(
            'links.prev', _ParseType.URL)
        """Link to previous JSON:API page in the query."""

        self.api_next_page_url: Union[str, None] = self._json.get(
            'links.next', _ParseType.URL)
        """Link to next JSON:API page in the query."""

        self.api_first_page_url: Union[str, None] = self._json.get(
            'links.first', _ParseType.URL)
        """Link to first JSON:API page in the query."""

        self.api_last_page_url: Union[str, None] = self._json.get(
            'links.last', _ParseType.URL)
        """Link to last JSON:API page in the query."""

        self.jsonapi_version: Union[str, None] = self._json.get(
            'jsonapi.version')
        """Version of the JSON:API specification of base API."""

        pr_count = len(self._data) if self._data else '0'
        logger.info(
            f'APIPage "{urllib.parse.unquote(self.request_url)}": '
            f'{pr_count} filings (of {self._data_count}), '
            f'{len(self._included_resources)} included subresources'
            )

    def _get_included_resources(self) -> list[_IncludedResource]:
        """Construct `_IncludedResource` objects from `included` key."""
        inc = self._json.get('included')
        resources = []
        if inc:
            res_frag: dict
            for res_frag in inc:
                res_type = str(res_frag.get('type')).lower()
                res_id = res_frag.get('id')
                if isinstance(res_id, str):
                    resources.append(
                        _IncludedResource(res_type, res_id, res_frag))
        return resources
