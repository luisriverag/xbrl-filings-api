"""Define `Entity` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import Prototype
from xbrl_filings_api.parse_type import ParseType
from xbrl_filings_api.scope_flag import ScopeFlag

if TYPE_CHECKING:
    from xbrl_filings_api.filing import Filing

__all__ = ['Entity']


class Entity(APIResource):
    """Entity (e.g. a group) in the database which has filed filings."""

    TYPE = 'entity'
    NAME = 'attributes.name'
    IDENTIFIER = 'attributes.identifier'
    API_ENTITY_FILINGS_URL = 'relationships.filings.links.related'

    _FILING_FLAG = ScopeFlag.GET_ENTITY

    def __init__(
            self,
            json_frag: Union[dict, Prototype],
            api_request: Optional[APIRequest] = None
            ) -> None:
        # Signatures::
        #     Entity(json_frag: dict, api_request: APIRequest)
        #     Entity(json_frag: Prototype)
        super().__init__(json_frag, api_request)

        self.identifier: Union[str, None] = self._json.get(self.IDENTIFIER)
        """
        The identifier for entity.

        For ESEF filers, this should be the LEI code.
        """

        self.name: Union[str, None] = self._json.get(self.NAME)
        """Name of the entity."""

        self.filings: set[Filing] = set()
        """Set of filings reported by this entity."""

        self.api_entity_filings_url: Union[str, None] = self._json.get(
            self.API_ENTITY_FILINGS_URL, ParseType.URL)
        r"""URL to the page with full list of filings by this entity."""

        self._json.close()

    def __repr__(self) -> str:
        """Return repr with `api_id` and `name`."""
        return (
            f'{type(self).__name__}('
            f'api_id={self.api_id!r}, name={self.name!r})'
            )

    def __str__(self) -> str:
        """
        Return "<`name`> (<`identifier`>)", or either alone.

        If both are defined, full string is returned but if only one is
        defined, it is returned. If neither is defined, return empty
        string.
        """
        if self.name and self.identifier:
            return f'{self.name} ({self.identifier})'
        if self.name:
            return self.name
        if self.identifier:
            return self.identifier
        return ''
