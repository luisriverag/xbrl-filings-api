"""Define function for constructing `DownloadSpecs` objects."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
from collections.abc import Container, Iterable, Mapping
from pathlib import PurePath
from typing import Any, Union

from xbrl_filings_api.download_info import DownloadInfo
from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.downloader import DownloadSpecs

logger = logging.getLogger(__name__)


def construct(
        files: Union[str, Iterable[str], Mapping[str, DownloadItem]],
        filing: Any,
        to_dir: Union[str, PurePath, None],
        stem_pattern: Union[str, None],
        valid_file_formats: Container,
        *,
        check_corruption: bool
        ) -> list[DownloadSpecs]:
    """
    Construct a list of `DownloadSpecs` objects.

    Returns
    -------
    DownloadSpecs
        Instructions for a concrete download.
    """
    if isinstance(files, str):
        files = [files]
    items = []

    if isinstance(files, Mapping):
        for format_key in files:
            download_item = files[format_key]
            full_item = _get_filing_download_specs(
                format_key, download_item, filing, to_dir, stem_pattern,
                valid_file_formats,
                check_corruption=check_corruption
                )
            if full_item:
                items.append(full_item)

    elif isinstance(files, Iterable):
        for file in files:
            full_item = _get_filing_download_specs(
                file, None, filing, to_dir, stem_pattern,
                valid_file_formats,
                check_corruption=check_corruption
                )
            if full_item:
                items.append(full_item)
    else:
        msg = "Parameter 'files' is neither a Mapping nor an Iterable"
        raise ValueError(msg)
    return items


def _get_filing_download_specs(
        file: str,
        download_item: Union[DownloadItem, None],
        filing: Any,
        to_dir: Union[str, PurePath, None],
        stem_pattern: Union[str, None],
        valid_file_formats: Container,
        *,
        check_corruption: bool
        ) -> Union[DownloadSpecs, None]:
    if file not in valid_file_formats:
        msg = f'file {file!r} is not among {valid_file_formats!r}'
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
