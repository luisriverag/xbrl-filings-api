"""
Define functions `assign` and `assign_single`.

Used to assign download path attributes of Filing objects to save paths.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable

from .exceptions import CorruptDownloadError


def assign_all(
        dlset: Iterable[tuple[object, str, str | Exception]]
        ) -> list[Exception] | None:
    """
    Assign saved paths to the filing objects.

    Parameters
    ----------
    dlset : iterable of tuples of (any, str, {str, Exception})
        Tuples of ``(filing, attr_base, result)`` where `result` is save
        path or exception.
    """
    excs = []
    for filing, attr_base, result in dlset:
        exc = assign_single(filing, attr_base, result)
        if exc:
            excs.append(exc)
    if excs:
        return excs
    return None


def assign_single(
        filing: object,
        attr_base: str,
        result: str | Exception
        ) -> Exception | None:
    exc: Exception | None = None
    save_path = None
    if isinstance(result, CorruptDownloadError):
        save_path = result.path
        exc = result
    elif isinstance(result, Exception):
        exc = result
    elif isinstance(result, str):
        save_path = result

    if save_path:
        setattr(filing, f'{attr_base}_download_path', save_path)
    return exc
