"""Define `Entity` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from typing import Union

from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import _Prototype
from xbrl_filings_api.enums import GET_ENTITY, _ParseType


class Entity(APIResource):
    """
    Entity of ``filings.xbrl.org`` API.

    Attributes
    ----------
    api_id : str or None
    identifier: Union[str, None]
    name: Union[str, None]
    filings: set of Filing
    api_entity_filings_url: Union[str, None]
    query_time : datetime
    request_url : str
    """

    TYPE: str = 'entity'
    NAME = 'attributes.name'
    IDENTIFIER = 'attributes.identifier'
    API_ENTITY_FILINGS_URL = 'relationships.filings.links.related'

    _FILING_FLAG = GET_ENTITY

    def __init__(
            self,
            json_frag: Union[dict, _Prototype],
            api_request: Union[_APIRequest, None] = None
            ) -> None:
        super().__init__(json_frag, api_request)

        self.identifier: Union[str, None] = self._json.get(self.IDENTIFIER)
        """
        The identifier for entity.

        For ESEF filers, this should be the LEI code.
        """

        self.name: Union[str, None] = self._json.get(self.NAME)
        """Name of the entity."""

        # Set of Filing objects
        self.filings: set[object] = set()
        """Set of `Filing` objects from the query reported by this
        entity.
        """

        self.api_entity_filings_url: Union[str, None] = self._json.get(
            self.API_ENTITY_FILINGS_URL, _ParseType.URL)
        """A link to the JSON:API page with full list of filings by this
        entity.
        """

        self._json.close()

    def __repr__(self) -> str:
        """Return string repr of the entity."""
        return f'{type(self).__name__}(name={self.name!r})'

    def __str__(self) -> str:
        """Return string str of the entity."""
        if self.name and self.identifier:
            return f'{self.name} ({self.identifier})'
        if self.name:
            return self.name
        if self.identifier:
            return self.identifier
        return ''
