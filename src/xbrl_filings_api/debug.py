# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from .api_object.json_tree import JSONTree
from .api_object.json_tree import KeyPathRetrieveCounts
import xbrl_filings_api.download_processor as download_processor
import xbrl_filings_api.request_processor as request_processor


def unaccessed_key_paths() -> list[tuple[str, str]]:
    """
    Get the list of unaccessed key paths in unserialized JSON
    fragments of API responses.
    
    For debugging API changes.

    Returns
    -------
    list of tuples (str, str)
        List of ordered tuples in form ``(class_qualname, key_path)``.
    """
    return sorted(JSONTree.get_unaccessed_key_paths())


def key_path_availability_counts() -> list[KeyPathRetrieveCounts]:
    """
    Get the list of successful retrieval counts for key paths in
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
    """Count of executed file downloads after importing the package."""
    return download_processor.item_counter


def api_request_count() -> int:
    """Count of executed API page requests after importing the package.
    """
    return request_processor.page_counter


def total_request_count() -> int:
    """Count of executed API page requests and file downloads after
    importing the package.
    """
    return download_count() + api_request_count()


def download_bytes() -> int:
    """Number of bytes downloaded excluding api requests after importing
    the package.
    """
    return download_processor.byte_counter


def download_size_str() -> str:
    """Number of bytes downloaded excluding api requests as byte
    multiples string after importing the package.
    """
    bcount = download_bytes()
    if bcount < 1024:
        return f'{bcount} B'
    if bcount < 1024 ** 2:
        return f'{round(bcount/1024, 2)} kB'
    if bcount < 1024 ** 3:
        return f'{round(bcount/1024**2, 2)} MB'
    else:
        return f'{round(bcount/1024**3, 2)} GB'
