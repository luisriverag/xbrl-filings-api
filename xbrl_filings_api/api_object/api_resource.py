"""
Define `APIResource` class.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from datetime import datetime
from types import EllipsisType
from typing import Any, Optional

from ..api_request import APIRequest
from ..constants import ATTRS_ALWAYS_EXCLUDE_FROM_DATA
from ..enums import ScopeFlag, GET_ONLY_FILINGS, GET_ENTITY
from .api_object import APIObject
import xbrl_filings_api.order_columns as order_columns


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

    TYPE: str | None = None
    _FILING_FLAG: ScopeFlag

    def __init__(
            self,
            json_frag: dict[str, Any] | EllipsisType,
            api_request: APIRequest | None = None
            ) -> None:
        """
        Initialize an API resource.

        Parameters
        ----------
        json_frag : dict or ellipsis
            JSON fragment in an API response. An ellipsis (...) may be
            given to create a prototype.
        """
        is_prototype = False
        if isinstance(json_frag, EllipsisType):
            is_prototype = True
            json_frag = {}
            api_request = APIRequest('', datetime.now())
        if api_request is None:
            raise ValueError()

        super().__init__(
            json_frag=json_frag,
            api_request=api_request,
            do_not_track=is_prototype
            )
        
        self.api_id: str | None = None
        api_id = self._json.get('id')
        if isinstance(api_id, str):
            self.api_id = api_id
        """``id`` from JSON:API."""

    @classmethod
    def get_data_attributes(
            cls, flags: Optional[ScopeFlag] = None,
            filings: Optional[Iterable['APIResource']] = None
            ) -> list[str]:
        """
        Get data attributes for an API resource subclass.

        Excludes internal and class attributes and the ones containing
        objects.

        For `Filing` objects this also means excluding attributes ending
        ``_download_path`` if all filings have this column filled with
        `None`. Additionally, if `GET_ENTITY` is not set filings will
        exclude `entity_api_id`.

        Parameters
        ----------
        flags : ScopeFlag, optional
            Only relevant for `Filing` resource type.
        filings : iterable of Filing, optional
            Only relevant for `Filing` resource type.
        """
        if cls is APIResource:
            raise NotImplementedError()
        resource_proto = cls(...)
        attrs = [
            attr for attr in dir(resource_proto)
            if not (
                attr.startswith('_')
                or getattr(cls, attr, False)
                or attr in ATTRS_ALWAYS_EXCLUDE_FROM_DATA)
            ]
        if cls.TYPE == 'filing':
            if filings:
                exclude_dlpaths = (
                    cls._get_unused_download_paths(filings))
                attrs = [attr for attr in attrs if attr not in exclude_dlpaths]
            if flags and GET_ENTITY not in flags:
                attrs.remove('entity_api_id')
        return order_columns.order_columns(attrs)

    @classmethod
    def _get_unused_download_paths(cls, filings: Iterable[Any]) -> set[str]:
        """
        Get unused `Filing` object attributes ending in ``_download_path``.

        Parameters
        ----------
        filings : iterable of Filing
        """
        fproto = cls(...)
        dlattrs = [
            att for att in dir(fproto)
            if not att.startswith('_') and att.endswith('_download_path')
            ]
        
        unused = set()
        for att in dlattrs:
            for fil in filings:
                if getattr(fil, att) is not None:
                    break
            else:
                unused.add(att)
        return unused

    @classmethod
    def get_columns(
            cls, has_entities: bool = False,
            filings: Iterable[Any] | None = None
            ) -> list[str]:
        """
        List of available columns for this `APIResource` subclass.

        Parameters
        ----------
        has_entities : bool, default False
            Only relevant for `Filing` objects.
        filings: iterable of Filing, optional
            Only relevant for `Filing` objects.
        """
        if cls is APIResource:
            raise NotImplementedError()
        flags = GET_ONLY_FILINGS
        if has_entities:
            flags = GET_ENTITY
        cols = cls.get_data_attributes(flags, filings)
        return order_columns.order_columns(cols)
