"""
Define `JSONTree`, `RetrieveCounter` and `KeyPathRetrieveCounts` class.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime, date, UTC
from typing import Optional
from urllib.parse import urljoin
import time

from ..enums import ParseType
import xbrl_filings_api.options as options


@dataclass
class RetrieveCounter:
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
    _unaccessed_paths: dict[str, set[str]] = dict()
    """``_unaccessed_paths[class_name] = {key_path1, key_path2, ...}``"""
    _object_path_counter: dict[str, dict[str, RetrieveCounter]] = dict()
    """``_object_path_counter[class_name][key_path] = RetrieveCounter()``"""
    unexpected_resource_types: set[tuple[str, str]] = set()
    """``unexpected_resource_types.pop() = (type_str, origin)``"""

    now = time.time()
    _local_utc_offset = (
        datetime.fromtimestamp(now) - datetime.utcfromtimestamp(now))
    del now

    def __init__(
            self,
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
        self.tree: dict | None = json_frag
        self.do_not_track = do_not_track

    def get(
            self, key_path: str, parse_type: Optional[ParseType] = None
            ) -> object | None:
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
            raise Exception(
                'Cannot call get() when JSONTree has been closed')
        key_value = None
        comps = key_path.split('.')
        subdict = self.tree
        last_part = len(comps) - 1
        for i, comp in enumerate(comps):
            key_value = subdict.get(comp)
            if i < last_part:
                subdict = key_value
                if subdict is None:
                    break
            else:
                if key_value is not None:
                    if parse_type == ParseType.DATETIME:
                        key_value = datetime.fromisoformat(key_value)
                        if options.utc_time:
                            key_value = key_value.astimezone(UTC)
                        else:
                            key_value = (
                                key_value.astimezone()
                                + self._local_utc_offset
                                )
                    if parse_type == ParseType.DATE:
                        parts = [int(part) for part in key_value.split('-')]
                        key_value = date(*parts)
                    elif parse_type == ParseType.URL:
                        key_value = urljoin(options.entry_point_url, key_value)
                break
        
        if not self.do_not_track:
            opcounter = self._object_path_counter
            if not opcounter.get(self.class_name):
                opcounter[self.class_name] = dict()
            
            if not opcounter[self.class_name].get(key_path):
                init_count = 0 if key_value is None else 1
                opcounter[self.class_name][key_path] = (
                    RetrieveCounter(success_count=init_count, total_count=1))
            
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
            raise Exception('Cannot close the same object more than once')
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
            raise Exception('close() cannot be called before get()')
        
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
    
    @classmethod
    def get_unaccessed_key_paths(cls) -> set[tuple[str, str]]:
        """Get the set of unaccessed key paths in unserialized JSON
        fragments of API responses."""
        unaccessed = set()
        for class_name, key_path_set in cls._unaccessed_paths.items():
            unaccessed.update(
                ((class_name, key_path) for key_path in key_path_set))
        return unaccessed

    @classmethod
    def get_key_path_availability_counts(cls) -> set[KeyPathRetrieveCounts]:
        """Get the set of successful retrieval counts for key paths in
        unserialized JSON fragments of API responses.
        """
        availability = set()
        for class_name, key_path_dict in cls._object_path_counter.items():
            availability.update((
                KeyPathRetrieveCounts(
                    class_name, key_path, counter.success_count,
                    counter.total_count
                    )
                for key_path, counter in key_path_dict.items()
                ))
        return availability
