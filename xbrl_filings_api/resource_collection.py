"""Define class `ResourceCollection`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable, Iterator
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional, Union

from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import DataAttributeType
from xbrl_filings_api.filing import Filing

if TYPE_CHECKING:
    from xbrl_filings_api.filing_set import FilingSet

__all__ = ['ResourceCollection']


class ResourceCollection:
    r"""
    :term:`Collection` of subresources of a `FilingSet` object.

    The subresources are all other `APIResource` subclasses except
    `Filing` objects.

    This object may be iterated over, it defines :func:`len` as well as
    operator ``in``. It may not, however, be accessed with an indexer
    (e.g. ``object[index]``) or :class:`reversed`.

    This collection is a view to the non-\ ``Filing`` resources of the
    parent ``FilingSet``, backreferenced in attribute `filingset`.

    `Entity` and `ValidationMessage` objects, as subclasses of
    `APIResource`, have a custom ``__hash__()`` method and their hash is
    based on a tuple of strings ``'APIResource'``, class attribute
    :py:attr:`~APIResource.TYPE`, and object
    :py:attr:`~APIResource.api_id`. This means that equality checks
    (``==``) and related methods are based on this tuple. For example,
    when the actual entity object is not available, a fast way to check
    if an entity with ``api_id`` ``'123'`` is included in the filing set
    ``fs`` is::

        ('APIResource', Entity.TYPE, '123') in fs.entities
    """

    def __init__(
            self, filingset: FilingSet, attr_name: str,
            item_class: type[APIResource]
            ) -> None:
        self.filingset: FilingSet = filingset
        """Reference to the parent `FilingSet` object."""

        self.item_class: type[APIResource] = item_class
        """Type object of the items within."""

        self._attr_name = attr_name
        self._columns: Union[list[str], None] = None

    @property
    def columns(self) -> list[str]:
        """List of available columns for resources of this type."""
        if self._columns:
            return self._columns
        self._columns = self.item_class.get_data_attributes()
        return self._columns

    @property
    def exist(self) -> bool:
        """
        True if any resources of this type exist.

        This property is faster than ``len(obj) != 0``.
        """
        filing: Filing
        # Attr `filingset` is always iterable (attr-defined)
        for filing in self.filingset: # type: ignore[attr-defined]
            if getattr(filing, self._attr_name):
                return True
        return False

    def get_pandas_data(
            self, attr_names: Optional[Iterable[str]] = None, *,
            strip_timezone: bool = True, date_as_datetime: bool = True,
            include_urls : bool = False
            ) -> dict[str, list[DataAttributeType]]:
        """
        Get resources as data for :class:`pandas.DataFrame` constructor.

        For example, a new dataframe can be instantiated for entities as
        follows::

            import pandas as pd
            df = pd.DataFrame(data=filingset.entities.get_pandas_data())

        If parameter ``attr_names`` is not given, most data attributes
        will be extracted.

        Parameters
        ----------
        attr_names: iterable of str, optional
            Valid attribute names of resource object.
        strip_timezone : bool, default True
            Strip timezone information (always UTC) from
            :class:`~datetime.datetime` values.
        date_as_datetime : bool, default True
            Convert :class:`~datetime.date` values to naive
            :class:`~datetime.datetime` to be converted to
            :class:`pandas.datetime64` by pandas.
        include_urls : bool, default False
            When parameter ``attr_names`` is not given, include
            attributes ending ``_url``.

        Returns
        -------
        data : dict of {str: list of DataAttributeType}
            Column names are the same as the attributes for resource of
            this type.

        See Also
        --------
        FilingSet.get_pandas_data : For `Filing` resources.
        """
        data: dict[str, list[DataAttributeType]]
        if attr_names:
            data = {col: [] for col in attr_names}
        else:
            data = {col: [] for col in self.columns}
            if not include_urls:
                url_cols = [col for col in data if col.endswith('_url')]
                for col in url_cols:
                    del data[col]
        for resource in self:
            for col_name in data:
                val = getattr(resource, col_name)
                if strip_timezone and isinstance(val, datetime):
                    val = val.replace(tzinfo=None)
                if (date_as_datetime
                        and isinstance(val, date)
                        and type(val) is not datetime):
                    val = datetime.fromordinal(val.toordinal())
                data[col_name].append(val)
        return data

    def __contains__(self, elem: Any) -> bool:
        """Return True if ResourceCollection contains ``elem``."""
        for ent in self:
            if ent == elem:
                return True
        return False

    def __iter__(self) -> Iterator[APIResource]:
        """Iterate ResourceCollection."""
        filing: Filing
        yielded_ids = set()
        # Attr `filingset` is always iterable (attr-defined)
        for filing in self.filingset: # type: ignore[attr-defined]
            attr_val = getattr(filing, self._attr_name)
            if attr_val:
                if isinstance(attr_val, set):
                    resource: APIResource
                    for resource in attr_val:
                        # Multiple filings cannot share validation
                        # messages, but here for completeness
                        if resource.api_id not in yielded_ids:
                            yielded_ids.add(resource.api_id)
                            yield resource
                elif attr_val.api_id not in yielded_ids:
                    yielded_ids.add(attr_val.api_id)
                    yield attr_val

    def __len__(self) -> int:
        """Return length of ResourceCollection."""
        count = 0
        for _ in self:
            count += 1
        return count

    def __repr__(self) -> str:
        """Return repr with `item_class` and ``len(self)``."""
        return (
            f'{type(self).__name__}('
            f'item_class={self.item_class!r}, '
            f'len(self)={len(self)})'
            )
