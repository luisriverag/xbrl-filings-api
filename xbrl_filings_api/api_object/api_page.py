"""
Define `APIPage` and `IncludedResource` classes.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.enums import ParseType


@dataclass(frozen=True)
class IncludedResource:
    type: str
    id: str
    frag: dict


class APIPage(APIObject):
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
    request_time : datetime
    request_url : str
    """

    def __init__(self, json_frag: dict, api_request: APIRequest):
        super().__init__(json_frag, api_request)

        self._data: list | None = self._json.get(
            'data')
        """List of main resources as unserialized JSON fragments of the
        page.
        """

        self._included_resources: list[IncludedResource] = (
            self._get_included_resources())
        """
        List of included resources as objects with fields `type`, `id`
        and `frag`.

        This list should be emptied and classified to class-specific
        attributes for sets of objects in the subclass `__init__`
        methods.
        """

        self._data_count: int | None = self._json.get(
            'meta.count')
        """Total count of total main resources of the query including
        the ones not on this page.
        """

        self.api_self_url: str | None = self._json.get(
            'links.self', ParseType.URL)
        """Link to this JSON:API page."""

        self.api_prev_page_url: str | None = self._json.get(
            'links.prev', ParseType.URL)
        """Link to previous JSON:API page in the query."""

        self.api_next_page_url: str | None = self._json.get(
            'links.next', ParseType.URL)
        """Link to next JSON:API page in the query."""

        self.api_first_page_url: str | None = self._json.get(
            'links.first', ParseType.URL)
        """Link to first JSON:API page in the query."""

        self.api_last_page_url: str | None = self._json.get(
            'links.last', ParseType.URL)
        """Link to last JSON:API page in the query."""

        self.jsonapi_version: str | None = self._json.get(
            'jsonapi.version')
        """Version of the JSON:API specification which this API follows."""

    def _get_included_resources(self) -> list[IncludedResource]:
        """Construct `IncludedResource` objects from `included` key."""
        inc = self._json.get('included')
        resources = []
        if inc:
            res_frag: dict
            for res_frag in inc:
                res_type = str(res_frag.get('type')).lower()
                res_id = res_frag.get('id')
                if isinstance(res_id, str):
                    resources.append(
                        IncludedResource(res_type, res_id, res_frag))
        return resources
