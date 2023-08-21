"""
Define `APIResource` class.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from types import EllipsisType
from typing import Any

from ..enums import ScopeFlag
from ..api_request import APIRequest
from .api_object import APIObject


class APIResource(APIObject):
    """
    A JSON:API resource.
    
    Subclasses of this class may be read into a database. An instance
    resembles a database record.
    
    Attributes
    ----------
    api_id : str or None
    request_time : datetime
    request_url : str
    """

    _FILING_FLAG: ScopeFlag

    def __init__(
            self,
            json_frag: dict[str, Any] | EllipsisType,
            api_request: APIRequest | None
            ) -> None:
        """
        Initialize an API resource.

        Parameters
        ----------
        json_frag : dict or ellipsis
            JSON fragment in an API response. An ellipsis (...) may be
            given to create a prototype.
        """
        is_prototype = (json_frag == Ellipsis)
        if is_prototype:
            json_frag = {}
            api_request = APIRequest('', datetime.now())
        json_frag: dict[str, Any]
        api_request: APIRequest

        super().__init__(
            json_frag=json_frag,
            api_request=api_request,
            do_not_track=is_prototype
            )
        
        self.api_id: str | None = None
        api_id = self._json.get('id')
        if isinstance(api_id, str):
            self.api_id: str | None = api_id
        """``id`` from JSON:API."""
