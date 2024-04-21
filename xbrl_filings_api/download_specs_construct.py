"""Define constructor for `downloader.DownloadSpecs` objects."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
from collections.abc import Iterable, Mapping
from pathlib import PurePath
from typing import Any, Union

from xbrl_filings_api.constants import FILE_STRING_CHOICE, FileStringType
from xbrl_filings_api.download_info import DownloadInfo
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.downloader import DownloadSpecs

__all__ = ['construct']

logger = logging.getLogger(__name__)


def construct(
        files: Union[
            FileStringType,
            Iterable[FileStringType],
            Mapping[FileStringType, DownloadItem]
            ],
        filing: Any,
        to_dir: Union[str, PurePath, None],
        stem_pattern: Union[str, None],
        *,
        check_corruption: bool,
        isfilingset: bool = False
        ) -> list[DownloadSpecs]:
    """
    Construct a list of `downloader.DownloadSpecs` objects.

    This function is used by methods ``download`` and ``download_aiter``
    of objects `Filing` and `FilingSet` to get a list of
    ``DownloadSpecs`` objects for calls to `downloader` subpackage
    functions.

    Returns
    -------
    downloader.DownloadSpecs
        Instructions for a concrete download.
    """
    if isinstance(files, str):
        files = [files]
    items = []

    if isinstance(files, Mapping):
        for file in files:
            download_item = files[file]
            full_item = _get_filing_download_specs(
                file, download_item, filing, to_dir, stem_pattern,
                check_corruption=check_corruption,
                isfilingset=isfilingset
                )
            if full_item:
                items.append(full_item)

    elif isinstance(files, Iterable):
        for file in files:
            # `file` is FileStringType, mypy mistakes for str due to
            # isinstance(files, str) in the beginning of the method
            full_item = _get_filing_download_specs(
                file, # type: ignore[arg-type]
                None, filing, to_dir, stem_pattern,
                check_corruption=check_corruption,
                isfilingset=isfilingset
                )
            if full_item:
                items.append(full_item)
    else:
        msg = "Parameter 'files' is none of str, Iterable or Mapping"
        raise TypeError(msg)
    return items


def _get_filing_download_specs(
        file: FileStringType,
        download_item: Union[DownloadItem, None],
        filing: Any,
        to_dir: Union[str, PurePath, None],
        stem_pattern: Union[str, None],
        *,
        check_corruption: bool,
        isfilingset: bool
        ) -> Union[DownloadSpecs, None]:
    if file not in FILE_STRING_CHOICE:
        msg = f'File {file!r} is not among {FILE_STRING_CHOICE!r}'
        raise ValueError(msg)

    url = getattr(filing, f'{file}_url')
    if not url:
        format_text = (
            file.capitalize() if file == 'package' else file.upper())
        msg = f'{format_text} not available for {filing!r}'
        logger.warning(msg, stacklevel=2)
        return None

    sha256 = None
    if check_corruption and file == 'package':
        sha256 = filing.package_sha256

    filename = None
    if download_item:
        if download_item.to_dir:
            to_dir = download_item.to_dir
        if download_item.stem_pattern:
            stem_pattern = download_item.stem_pattern
        if download_item.filename:
            if isfilingset:
                msg = (
                    'The attribute DownloadItem.filename may not be other '
                    'than None when calling FilingSet methods.'
                    )
                raise ValueError(msg)
            filename = download_item.filename
    if not to_dir:
        to_dir = '.'

    return DownloadSpecs(
        url=url,
        to_dir=to_dir,
        stem_pattern=stem_pattern,
        filename=filename,
        sha256=sha256,
        info=DownloadInfo(obj=filing, file=file)
        )
