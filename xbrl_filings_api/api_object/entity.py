"""
Define `Entity` class.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from types import EllipsisType

from ..enums import ParseType, GET_ENTITY
from ..api_request import APIRequest
from .api_resource import APIResource


class Entity(APIResource):
    """
    Entity of ``filings.xbrl.org`` API.
    
    Attributes
    ----------
    api_id : str or None
    identifier: str | None
    name: str | None
    filings: set of Filing
    api_entity_filings_url: str | None
    request_time : datetime
    request_url : str
    """
    
    TYPE: str = 'entity'
    NAME = 'attributes.name'
    IDENTIFIER = 'attributes.identifier'
    API_ENTITY_FILINGS_URL = 'relationships.filings.links.related'

    _FILING_FLAG = GET_ENTITY

    def __init__(
            self,
            json_frag: dict | EllipsisType,
            api_request: APIRequest | None = None
            ) -> None:
        super().__init__(json_frag, api_request)

        self.identifier: str | None = self._json.get(self.IDENTIFIER)
        """
        The identifier for entity.
        
        For ESEF filers, this is the LEI code.
        """

        self.name: str | None = self._json.get(self.NAME)
        """Name of the entity."""

        # Set of Filing objects
        self.filings: set[object] = set()
        """Set of `Filing` objects from the query reported by this
        entity.
        """

        self.api_entity_filings_url: str | None = self._json.get(
            self.API_ENTITY_FILINGS_URL, ParseType.URL)
        """A link to the JSON:API page with full list of filings by this
        entity.
        """
        
        self._json.close()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name!r})'
