"""Define debugging functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from xbrl_filings_api.json_tree import KeyPathRetrieveCounts, _JSONTree


def get_unaccessed_key_paths() -> list[tuple[str, str]]:
    """
    Get unaccessed JSON key paths of objects.

    Get the list of unaccessed key paths in unserialized JSON fragments
    of API responses. List values (JSON arrays) are listed as a single
    path.

    Does not record the unaccessed paths if `_JSONTree` of the
    `APIObject` has been initialized with `do_not_track` value `True`.

    For debugging API changes.

    Returns
    -------
    list of tuples (str, str)
        List of ordered tuples in form ``(class_qualname, key_path)``.
    """
    return sorted(_JSONTree.get_unaccessed_key_paths())


def get_key_path_availability_counts() -> list[KeyPathRetrieveCounts]:
    """
    Get counts of key paths that did not resolve to `None`.

    Get the list of successful retrieval counts for key paths in
    unserialized JSON fragments of API responses.

    Does not record the unaccessed paths if `_JSONTree` of the
    `APIObject` has been initialized with `do_not_track` value `True`.

    For debugging API changes.

    The `KeyPathRetrieveCounts` objects contain the attributes
    `class_name` (str), `key_path` (str), `success_count` (int) and
    `total_count` (int).

    Returns
    -------
    list of KeyPathRetrieveCounts
        List of ordered retrieve counts for key paths of different
        API objects.
    """
    return sorted(_JSONTree.get_key_path_availability_counts())


def get_unexpected_resource_types() -> list[tuple[str, str]]:
    """
    Get unexpected resource types from the API.

    `_JSONTree` initialization attribute `do_not_track` has no effect.

    Returns
    -------
    list of tuples (str, str)
        List of ordered tuples in form ``(type_str, origin)``.
    """
    return sorted(_JSONTree.unexpected_resource_types)
