"""Define `APIPage` and `IncludedResource` classes."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import urllib
from dataclasses import dataclass
from typing import Union

from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.enums import _ParseType

__all__ = [
    'IncludedResource',
    'APIPage',
    ]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IncludedResource:
    """Dataclass for storing element in ``included`` section of page."""

    type_: str
    id_: str
    frag: dict


class APIPage(APIObject):
    r"""Base class for JSON:API response page or document."""

    def __init__(self, json_frag: dict, api_request: APIRequest):
        if type(self) is APIPage:
            msg = 'APIPage can only be initialized via subclassing'
            raise NotImplementedError(msg)

        super().__init__(json_frag, api_request)

        self.api_self_url: Union[str, None] = self._json.get(
            'links.self', _ParseType.URL)
        """URL to this `APIPage`."""

        self.api_prev_page_url: Union[str, None] = self._json.get(
            'links.prev', _ParseType.URL)
        """URL to previous `APIPage` in the query."""

        self.api_next_page_url: Union[str, None] = self._json.get(
            'links.next', _ParseType.URL)
        """URL to next `APIPage` in the query."""

        self.api_first_page_url: Union[str, None] = self._json.get(
            'links.first', _ParseType.URL)
        """URL to first `APIPage` in the query."""

        self.api_last_page_url: Union[str, None] = self._json.get(
            'links.last', _ParseType.URL)
        """URL to last `APIPage` in the query."""

        self.jsonapi_version: Union[str, None] = self._json.get(
            'jsonapi.version')
        r"""Version of the JSON-API protocol used on this `APIPage`."""

        self._data: Union[list, None] = self._json.get(
            'data')
        """List of main resources as unserialized JSON fragments of the
        page.
        """

        self._ensure_data_ids_are_strings()

        self._included_resources: list[IncludedResource] = (
            self._get_included_resources())
        """
        List of page subresources from ``included`` key.

        This list should be emptied and classified to class-specific
        attributes for sets of objects in the subclass `__init__`
        methods.
        """

        self._data_count: Union[int, None] = self._json.get(
            'meta.count')
        """Total count of total main resources of the query including
        the ones not on this page.
        """

        pr_count = len(self._data) if self._data else '0'
        logger.info(
            f'APIPage "{urllib.parse.unquote(self.request_url)}": '
            f'{pr_count} filings (of {self._data_count}), '
            f'{len(self._included_resources)} included subresources'
            )

    def _get_included_resources(self) -> list[IncludedResource]:
        """Construct `IncludedResource` objects from ``included``."""
        inc = self._json.get('included')
        resources = []
        if inc:
            res_frag: dict
            for res_frag in inc:
                res_type = str(res_frag.get('type')).lower()
                res_id = res_frag.get('id')
                if not isinstance(res_id, str):
                    res_id = str(res_id)
                resources.append(
                    IncludedResource(res_type, res_id, res_frag))
        return resources

    def _ensure_data_ids_are_strings(self):
        for data_frag in self._data:
            api_id = data_frag.get('id')
            if not isinstance(api_id, str):
                data_frag['id'] = str(api_id)
