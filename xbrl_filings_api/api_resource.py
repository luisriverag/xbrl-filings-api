"""Define `APIResource` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Optional, Union

from xbrl_filings_api import order_columns
from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.constants import (
    ATTRS_ALWAYS_EXCLUDE_FROM_DATA,
    PROTOTYPE,
    Prototype,
)
from xbrl_filings_api.scope_flag import ScopeFlag

__all__ = ['APIResource']

UTC = timezone.utc


class APIResource(APIObject):
    """
    Base class for JSON:API resources, i.e., data objects.

    Subclasses of this class may be read into a database. An instance
    resembles a database record.

    This library assumes the API returning datetimes in UTC, if no
    timezone is specified (situation as of April 2024). Original
    datetime string is retained in attribute with ``"_time_str"`` ending
    paired with the ``"_time"`` ended attributes (e.g.
    `added_time_str`).
    """

    TYPE: str = ''
    """JSON-API resource ``type`` of `APIResource` subclass."""

    _FILING_FLAG: ScopeFlag

    def __init__(
            self,
            json_frag: Union[dict, Prototype],
            api_request: Union[APIRequest, None] = None
            ) -> None:
        # Constructing with only `PROTOTYPE` as an argument creates a
        # dummy object with instance attributes.
        if type(self) is APIResource:
            msg = 'APIResource can only be initialized via subclassing'
            raise NotImplementedError(msg)

        is_prototype = False
        if json_frag == PROTOTYPE:
            is_prototype = True
            json_frag = {}
            api_request = APIRequest('', datetime.now(UTC))
        if api_request is None:
            msg = 'Parameter api_request not given'
            raise ValueError(msg)

        super().__init__(
            json_frag=json_frag, # type: ignore[arg-type] # Never PROTOTYPE
            api_request=api_request,
            do_not_track=is_prototype
            )

        api_id = self._json.get('id')
        self.api_id: str = str(api_id)
        r"""
        JSON-API resource ``id`` of `APIResource`.

        Can be used as a unique identifier among resources of the same
        type.
        """

        self._hash = hash(('APIResource', self.TYPE, self.api_id))

    @classmethod
    def get_data_attributes(
            cls, flags: Optional[ScopeFlag] = None,
            filings: Optional[Iterable['APIResource']] = None
            ) -> list[str]:
        """
        Return data attributes for an `APIResource`.

        Excludes internal and class attributes and the ones containing
        objects.

        For `Filing` objects this also means excluding attributes ending
        ``_download_path`` if every filing in parameter ``filings`` have
        this attribute as :pt:`None`. Additionally, if `GET_ENTITY`
        is not included in parameter ``flags``, returned attribute list
        will exclude `entity_api_id`.

        Parameters
        ----------
        flags : ScopeFlag, optional
            Used to exclude attribute `Filing.entity_api_id`.
        filings : iterable of Filing, optional
            Used to exclude `Filing` attributes ending
            ``_download_path``.

        Returns
        -------
        list of str
            List of data attributes.
        """
        if cls is APIResource:
            raise NotImplementedError()
        resource_proto = cls(PROTOTYPE)
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

    def __eq__(self, other: Any) -> bool:
        """Return :pt:`True` when both __hash__() match."""
        return self._hash == hash(other)

    def __hash__(self):
        """Return hash of ``('APIResource', cls.TYPE, self.api_id)``."""
        return self._hash

    @classmethod
    def _get_unused_download_paths(cls, filings: Iterable[Any]) -> set[str]:
        """
        Get unused `Filing` object download path attributes.

        Looks for attributes ending in ``_download_path``.

        Parameters
        ----------
        filings : iterable of Filing
        """
        fproto = cls(PROTOTYPE)
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
