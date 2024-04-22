"""Define debugging functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from xbrl_filings_api.json_tree import JSONTree, KeyPathRetrieveCounts

__all__ = [
    'get_key_path_availability_counts',
    'get_unaccessed_key_paths',
    'get_unexpected_resource_types'
    ]


def get_key_path_availability_counts() -> list[KeyPathRetrieveCounts]:
    """
    Get counts of dot access paths that did not resolve to :pt:`None`.

    Get the list of successful retrieval counts for dot access paths in
    JSON fragments of API responses.

    Does not record the unaccessed paths if `JSONTree` of the
    `APIObject` has been initialized with ``do_not_track`` value
    :pt:`True`.

    For debugging API changes.

    Returns
    -------
    list of KeyPathRetrieveCounts
        List of ordered retrieve counts for key paths of different
        API objects.
    """
    return sorted(JSONTree.get_key_path_availability_counts())


def get_unaccessed_key_paths() -> list[tuple[str, str]]:
    """
    Get unaccessed dot access paths of JSON objects.

    Get the list of unaccessed dot access paths in JSON fragments of API
    responses. List values (JSON arrays) are listed as a single path.

    Does not record the unaccessed paths if `JSONTree` of the
    `APIObject` has been initialized with ``do_not_track`` value
    :pt:`True`.

    For debugging API changes.

    Returns
    -------
    list of tuple (str, str)
        List of ordered tuples in form :pt:`(class_qualname, key_path)`.
    """
    return sorted(JSONTree.get_unaccessed_key_paths())


def get_unexpected_resource_types() -> list[tuple[str, str]]:
    """
    Get unexpected resource types from the API.

    `JSONTree` initialization parameter ``do_not_track`` has no effect.

    Returns
    -------
    list of tuple (str, str)
        List of ordered tuples in form :pt:`(type_str, origin)`.
    """
    return sorted(JSONTree.unexpected_resource_types)
