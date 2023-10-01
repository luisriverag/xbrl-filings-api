"""Define class `ResourceCollection`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Iterator
from typing import Any, Optional, Union

from xbrl_filings_api.api_resource import APIResource
from xbrl_filings_api.constants import ResourceLiteralType
from xbrl_filings_api.filing import Filing


class ResourceCollection:
    """
    Collection of subresources of a `FilingSet` object.

    The subresources are all other `APIResource` subclasses except
    `Filing` objects.

    This object is a `collections.abc.Collection` which means it may be
    iterated over, it defines `len()` as well as operator `in`. It may
    not, however, be accessed with an indexer (e.g. `object[index]`) or
    reversed.

    This collection is a view to the resources of the parent
    `FilingSet`. Adding or removing filings from the parent will change
    the set of resources in this collection.

    Attributes
    ----------
    parent : FilingSet
    get_pandas_data : dict of str: list of ResourceLiteralType
    columns : list of str
    exist : bool
    """

    def __init__(
            self, parent: Any, attr_name: str, type_obj: type[APIResource]
            ) -> None:
        # FilingSet object
        self.parent = parent

        self._attr_name = attr_name
        self._type_obj = type_obj
        self._columns: Union[list[str], None] = None

    def __iter__(self) -> Iterator[APIResource]:
        """Return iterator for subresources."""
        filing: Filing
        yielded_ids = set()
        for filing in self.parent:
            attr_val = getattr(filing, self._attr_name)
            if attr_val:
                if isinstance(attr_val, set):
                    resource: APIResource
                    for resource in attr_val:
                        if resource.api_id not in yielded_ids:
                            yielded_ids.add(resource.api_id)
                            yield resource
                elif attr_val.api_id not in yielded_ids:
                    yielded_ids.add(attr_val.api_id)
                    yield attr_val

    def __len__(self) -> int:
        """Return count of subresources."""
        count = 0
        for _ in self:
            count += 1
        return count

    def __contains__(self, item: Any) -> bool:
        """Return `True` if `item` exists in collection."""
        for resource in self:
            if resource is item:
                return True
        return False

    def get_pandas_data(
            self, attr_names: Optional[Iterable[str]] = None
            ) -> dict[str, list[ResourceLiteralType]]:
        """
        Get data for `pandas.DataFrame` constructor for objects.

        A new dataframe can be instantiated by::

            pandas.DataFrame(
                data=filingset.collection_name.get_pandas_data())

        If `attr_names` is not given, most data attributes will be
        extracted. Attributes ending in ``_download_path`` will be
        extracted only if at least one file of this type has been
        downloaded and `entity_api_id` if there is at least one entity
        object in the set.

        Parameters
        ----------
        attr_names: iterable of str, optional
            Valid attribute names of resource object.

        Returns
        -------
        dict of str: list of ResourceLiteralType
            Column names are the same as the attributes for resource of
            this type.
        """
        data: dict[str, list[ResourceLiteralType]]
        if attr_names:
            data = {col: [] for col in attr_names}
        else:
            data = {col: [] for col in self.columns}
        for resource in self:
            for col_name in data:
                data[col_name].append(getattr(resource, col_name))
        return data

    @property
    def columns(self) -> list[str]:
        """List of available columns for resources of this type."""
        if self._columns:
            return self._columns
        self._columns = self._type_obj.get_columns()
        return self._columns

    @property
    def exist(self) -> bool:
        """
        True if any resources of this type exist.

        This property is faster than ``len(obj) != 0``.
        """
        filing: Filing
        for filing in self.parent:
            if getattr(filing, self._attr_name):
                return True
        return False
