"""Define `APIResource` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Optional, Union, overload

from xbrl_filings_api import order_columns
from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.constants import (
    _PROTOTYPE,
    ATTRS_ALWAYS_EXCLUDE_FROM_DATA,
    _Prototype,
)
from xbrl_filings_api.enums import ScopeFlag

UTC = timezone.utc


class APIResource(APIObject):
    """
    A JSON:API resource.

    Subclasses of this class may be read into a database. An instance
    resembles a database record.

    Attributes
    ----------
    api_id : str or None
    query_time : datetime
    request_url : str
    """

    TYPE: Union[str, None] = None
    _FILING_FLAG: ScopeFlag

    @overload
    def __init__(self, json_frag: _Prototype) -> None: ...
    @overload
    def __init__(self, json_frag: dict, api_request: _APIRequest) -> None: ...
    def __init__(
            self,
            json_frag: Union[dict, _Prototype],
            api_request: Union[_APIRequest, None] = None
            ) -> None:
        """
        Initialize an API resource.

        Parameters
        ----------
        json_frag : dict or _PROTOTYPE
            JSON fragment in an API response. `_PROTOTYPE` constant may
            be given to create a dummy instance.
        """
        if type(self) is APIResource:
            msg = 'APIResource can only be initialized via subclassing'
            raise NotImplementedError(msg)

        is_prototype = False
        if json_frag == _PROTOTYPE:
            is_prototype = True
            json_frag = {}
            api_request = _APIRequest('', datetime.now(UTC))
        if api_request is None:
            msg = 'Parameter api_request not given'
            raise ValueError(msg)

        super().__init__(
            json_frag=json_frag, # type: ignore[arg-type] # Never _PROTOTYPE
            api_request=api_request,
            do_not_track=is_prototype
            )

        self.api_id: Union[str, None] = None
        """``id`` from JSON:API."""

        api_id = self._json.get('id')
        self.api_id = str(api_id)

        self._hash = hash(('APIResource', self.TYPE, self.api_id))

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
        ``_download_path`` if all `filings` have this column filled with
        `None`. Additionally, if `GET_ENTITY` is not included in
        `flags`, filings will exclude `entity_api_id`.

        Parameters
        ----------
        flags : ScopeFlag, optional
            Only relevant for `Filing` resource type. See remarks above.
        filings : iterable of Filing, optional
            Only relevant for `Filing` resource type. See remarks above.
        """
        if cls is APIResource:
            raise NotImplementedError()
        resource_proto = cls(_PROTOTYPE)
        attrs = [
            attr for attr in dir(resource_proto)
            if not (
                attr.startswith('_')
                or attr.endswith('_time_str')
                or getattr(cls, attr, False)
                or attr in ATTRS_ALWAYS_EXCLUDE_FROM_DATA)
            ]
        if cls.TYPE == 'filing':
            if filings:
                exclude_dlpaths = (
                    cls._get_unused_download_paths(filings))
                attrs = [attr for attr in attrs if attr not in exclude_dlpaths]
            if not flags or ScopeFlag.GET_ENTITY not in flags:
                attrs.remove('entity_api_id')
        return order_columns.order_columns(attrs)

    @classmethod
    def _get_unused_download_paths(cls, filings: Iterable[Any]) -> set[str]:
        """
        Get unused `Filing` object download path attributes.

        Looks for attributes ending in ``_download_path``.

        Parameters
        ----------
        filings : iterable of Filing
        """
        fproto = cls(_PROTOTYPE)
        dlattrs = [
            att for att in dir(fproto)
            if not att.startswith('_') and att.endswith('_download_path')
            ]

        unused = set()
        for attr_name in dlattrs:
            for filing in filings:
                if getattr(filing, attr_name) is not None:
                    break
            else:
                unused.add(attr_name)
        return unused

    @classmethod
    def get_columns(
            cls, *, filings: Union[Iterable[Any], None] = None,
            has_entities: bool = False
            ) -> list[str]:
        """
        List of available columns for this `APIResource` subclass.

        Parameters
        ----------
        filings: iterable of Filing, optional
            Only relevant for `Filing` objects.
        has_entities : bool, default False
            Only relevant for `Filing` objects.
        """
        if cls is APIResource:
            raise NotImplementedError()
        flags = ScopeFlag.GET_ONLY_FILINGS
        if has_entities:
            flags = ScopeFlag.GET_ENTITY
        cols = cls.get_data_attributes(flags, filings)
        return cols

    def __eq__(self, other: Any) -> bool:
        """Return true when hashes match."""
        return self._hash == hash(other)

    def __hash__(self):
        """Return hash of tuple `('APIResource', TYPE, api_id)`."""
        return self._hash
