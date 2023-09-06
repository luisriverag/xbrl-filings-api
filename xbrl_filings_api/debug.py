"""Define debugging functions."""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import xbrl_filings_api.downloader as downloader
import xbrl_filings_api.request_processor as request_processor
from xbrl_filings_api.api_object import (
    JSONTree,
    KeyPathRetrieveCounts,
)


def unaccessed_key_paths() -> list[tuple[str, str]]:
    """
    Get unaccessed JSON key paths of objects.

    Get the set of unaccessed key paths in unserialized JSON fragments
    of API responses.

    For debugging API changes.

    Returns
    -------
    list of tuples (str, str)
        List of ordered tuples in form ``(class_qualname, key_path)``.
    """
    return sorted(JSONTree.get_unaccessed_key_paths())


def key_path_availability_counts() -> list[KeyPathRetrieveCounts]:
    """
    Get counts of key paths that did not resolve to `None`.

    Get the set of successful retrieval counts for key paths in
    unserialized JSON fragments of API responses.

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
    return sorted(JSONTree.get_key_path_availability_counts())


def unexpected_resource_types() -> list[tuple[str, str]]:
    """
    Get unexpected resource types from the API.

    Returns
    -------
    list of tuples (str, str)
        List of ordered tuples in form ``(type_str, origin)``.
    """
    return sorted(JSONTree.unexpected_resource_types)


def download_count() -> int:
    """
    Return count of finished file downloads.

    Counter starts when the package is imported for the first time.
    """
    return downloader.stats.item_counter


def api_request_count() -> int:
    """
    Return count of executed API page requests.

    A single query may include multiple requests. Counter starts when
    the package is imported for the first time.
    """
    return request_processor.page_counter


def total_request_count() -> int:
    """
    Return count of finished API page requests and file downloads.

    Counter starts when the package is imported for the first time.
    """
    return download_count() + api_request_count()


def download_bytes() -> int:
    """
    Return number of bytes downloaded excluding API requests.

    Counter starts when the package is imported for the first time.
    """
    return downloader.stats.byte_counter


def download_size_str() -> str:
    """
    Return size of data downloaded as text excluding API requests.

    Scale units used are powers of 1024.

    Counter starts when the package is imported for the first time.
    """
    kb = 1024
    bcount = download_bytes()
    if bcount < kb:
        return f'{bcount} B'
    if bcount < kb ** 2:
        return f'{round(bcount/kb, 2)} kB'
    if bcount < kb ** 3:
        return f'{round(bcount/kb**2, 2)} MB'
    else:
        return f'{round(bcount/kb**3, 2)} GB'
