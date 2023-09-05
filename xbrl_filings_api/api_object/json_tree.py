"""
Define `JSONTree`, `_RetrieveCounter` and `KeyPathRetrieveCounts` class.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import time
import warnings
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, ClassVar, Optional
from urllib.parse import urljoin

import xbrl_filings_api.options as options
from xbrl_filings_api.enums import ParseType
from xbrl_filings_api.exceptions import APIStringParseWarning


@dataclass
class _RetrieveCounter:
    success_count: int
    total_count: int


@dataclass(order=True, frozen=True)
class KeyPathRetrieveCounts:
    class_name: str
    key_path: str
    success_count: int
    total_count: int


class JSONTree:
    """
    Reader for deeply nested deserialized JSON trees.

    When the required keys have been read, `close()` method must be
    called in the init methods of leaf subclasses of `APIObject`. This
    ensures that the keys which were never accessed (novel API features)
    are available for `get_unaccessed_key_paths()` method.

    Attributes
    ----------
    class_name : str
    tree : dict or None
    do_not_track : bool
    """
    _unaccessed_paths: ClassVar[dict[str, set[str]]] = {}
    """``_unaccessed_paths[class_name] = {key_path1, key_path2, ...}``"""
    _object_path_counter: ClassVar[dict[str, dict[str, _RetrieveCounter]]] = {}
    """``_object_path_counter[class_name][key_path] = _RetrieveCounter()``"""
    unexpected_resource_types: ClassVar[set[tuple[str, str]]] = set()
    """``unexpected_resource_types.pop() = (type_str, origin)``"""

    now = time.time()
    _local_utc_offset = (
        datetime.fromtimestamp(now)
        - datetime.utcfromtimestamp(now)
        ) # type: ignore
    del now

    def __init__(
            self,
            *,
            class_name: str,
            json_frag: dict | None,
            do_not_track: bool = False
            ) -> None:
        """
        Initialize a JSONTree instance.

        Parameters
        ----------
        class_name : str
            The `__qualname__` of the parent `APIObject` subclass.
        json_frag : dict or None
            The underlying JSON:API unserialized JSON as a dictionary
            structure. An `APIPage` contains the whole document.
        do_not_track : bool, default False
            Do not track read and unaccessed keys.
        """
        self.class_name = class_name
        self.tree: dict[str, Any] | None = json_frag
        self.do_not_track = do_not_track

    def get(
            self, key_path: str, parse_type: Optional[ParseType] = None
            ) -> Any:
        """
        Read a dictionary key from a deeply nested dictionary.

        Parameters
        ----------
        key_path : str
            A dot-delimited key path for navigation in a deeply nested
            serialized JSON object.
            E.g. 'relationships.validation_messages.links.related'.
        parse_type : ParseType member, optional
            One of the `ParseType` Enum members. `ParseType.DATETIME`
            parses locale-aware ISO style UTC strings such as
            '2023-05-09 10:51:50.382633', `ParseType.DATE` parses naive
            dates and `ParseType.URL` resolves relative URLs based on
            option `entry_point_url`.
        """
        if self.tree is None:
            msg = 'Cannot call get() when JSONTree has been closed'
            raise Exception(msg)
        key_value = None
        comps = key_path.split('.')
        subdict: dict[str, Any] = self.tree
        last_part = len(comps) - 1
        for i, comp in enumerate(comps):
            key_value = subdict.get(comp)
            if key_value is None:
                break
            elif isinstance(key_value, dict):
                if i < last_part:
                    subdict = key_value
                else:
                    # Value of key_path is dict
                    break
            # Get actual existing non-dict value of key_path
            else:
                if isinstance(key_value, str):
                    key_value = self._parse_value(
                        key_value, parse_type, key_path)
                break

        if not self.do_not_track:
            opcounter = self._object_path_counter
            if not opcounter.get(self.class_name):
                opcounter[self.class_name] = {}

            if not opcounter[self.class_name].get(key_path):
                init_count = 0 if key_value is None else 1
                opcounter[self.class_name][key_path] = (
                    _RetrieveCounter(success_count=init_count, total_count=1))

            else:
                counter = opcounter[self.class_name][key_path]
                if key_value is not None:
                    counter.success_count += 1
                counter.total_count += 1
        return key_value

    def close(self) -> None:
        """Remember all unaccessed and never existing key paths in the
        nested dictionary structure but skip lists.
        """
        if self.do_not_track:
            return
        if self.tree is None:
            msg = 'Cannot close the same object more than once'
            raise Exception(msg)
        for key in self.tree:
            self._find_unaccessed(self.tree, [key])
        self.tree = None

    def _find_unaccessed(
            self, json_frag: dict, comps: list[str]) -> None:
        """Traverse the whole JSON tree/fragment by recursion, skip
        lists.
        """
        opcounter = self._object_path_counter
        if opcounter.get(self.class_name) is None:
            msg = 'close() cannot be called before get()'
            raise Exception(msg)

        last_comp = comps[len(comps) - 1]
        key_value = json_frag.get(last_comp)
        if isinstance(key_value, dict):
            for key in key_value:
                comps_copy = comps.copy()
                comps_copy.append(key)
                self._find_unaccessed(key_value, comps_copy)
        elif '.'.join(comps) not in opcounter[self.class_name]:
            upaths = self._unaccessed_paths
            if not upaths.get(self.class_name):
                upaths[self.class_name] = set()
            upaths[self.class_name].add('.'.join(comps))

    def _parse_value(
            self, key_value: str, parse_type: ParseType | None, key_path: str
            ) -> datetime | date | str | None:
        """Parse string value of `key_path` based on `parse_type`."""
        if parse_type == ParseType.DATETIME:
            parsed_dt = None
            try:
                parsed_dt = datetime.fromisoformat(key_value)
            except ValueError:
                msg = (
                    f'Could not parse ISO datetime string {key_value!r} for '
                    f'object {self.class_name} JSON fragment path {key_path!r}.'
                    )
                warnings.warn(msg, APIStringParseWarning, stacklevel=2)
            if parsed_dt is None:
                return None
            if options.utc_time:
                return parsed_dt.astimezone(UTC)
            else:
                return (
                    parsed_dt.astimezone()
                    + self._local_utc_offset
                    )

        if parse_type == ParseType.DATE:
            parsed_date = None
            try:
                parts = [int(part) for part in key_value.split('-')]
                parsed_date = date(*parts)
            except ValueError:
                msg = (
                    f'Could not parse ISO date string {key_value!r} for '
                    f'object {self.class_name} JSON fragment path {key_path!r}.'
                    )
                warnings.warn(msg, APIStringParseWarning, stacklevel=2)
            return parsed_date

        if parse_type == ParseType.URL:
            parsed_url = None
            try:
                parsed_url = urljoin(options.entry_point_url, key_value)
            except ValueError:
                msg = (
                    f'Could not determine absolute URL string from '
                    f'{key_value!r} for object {self.class_name} JSON '
                    f'fragment path {key_path!r}.'
                    )
                warnings.warn(msg, APIStringParseWarning, stacklevel=2)
            return parsed_url

        return key_value

    @classmethod
    def get_unaccessed_key_paths(cls) -> set[tuple[str, str]]:
        """Get the set of unaccessed key paths in unserialized JSON
        fragments of API responses."""
        unaccessed: set[tuple[str, str]] = set()
        for class_name, key_path_set in cls._unaccessed_paths.items():
            unaccessed.update(
                (class_name, key_path) for key_path in key_path_set)
        return unaccessed

    @classmethod
    def get_key_path_availability_counts(cls) -> set[KeyPathRetrieveCounts]:
        """Get the set of successful retrieval counts for key paths in
        unserialized JSON fragments of API responses.
        """
        availability: set[KeyPathRetrieveCounts] = set()
        for class_name, key_path_dict in cls._object_path_counter.items():
            availability.update((
                KeyPathRetrieveCounts(
                    class_name, key_path, counter.success_count,
                    counter.total_count
                    )
                for key_path, counter in key_path_dict.items()
                ))
        return availability
