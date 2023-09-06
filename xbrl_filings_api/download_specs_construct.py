"""Define function for constructing `DownloadSpecs` objects."""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import warnings
from collections.abc import Container, Iterable, Mapping
from pathlib import PurePath
from typing import Any

from xbrl_filings_api.download_item import DownloadItem
from xbrl_filings_api.downloader import DownloadSpecs
from xbrl_filings_api.exceptions import FileNotAvailableWarning


def construct(
        formats: str | Iterable[str] | Mapping[str, DownloadItem],
        filing: Any,
        to_dir: str | PurePath | None,
        stem_pattern: str | None,
        filename: str | None,
        valid_formats: Container,
        *,
        check_corruption: bool
        ) -> list[DownloadSpecs]:
    """Construct a list of `DownloadSpecs` objects."""
    if isinstance(formats, str):
        formats = [formats]
    items = []

    if isinstance(formats, Mapping):
        for format_key in formats:
            download_item = formats[format_key]
            full_item = _get_filing_download_specs(
                format_key, download_item, filing, to_dir, stem_pattern,
                filename, valid_formats,
                check_corruption=check_corruption
                )
            if full_item:
                items.append(full_item)

    elif isinstance(formats, Iterable):
        for format_ in formats:
            full_item = _get_filing_download_specs(
                format_, None, filing, to_dir, stem_pattern, filename,
                valid_formats,
                check_corruption=check_corruption
                )
            if full_item:
                items.append(full_item)
    else:
        msg = "Parameter 'formats' is neither a Mapping nor an Iterable"
        raise ValueError(msg)
    return items


def _get_filing_download_specs(
        format_: str,
        download_item: DownloadItem | None,
        filing: Any,
        to_dir: str | PurePath | None,
        stem_pattern: str | None,
        filename: str | None,
        valid_formats: Container,
        *,
        check_corruption: bool
        ) -> DownloadSpecs | None:
    if format_ not in valid_formats:
        msg = f'Format_ {format_!r} is not among {valid_formats!r}'
        raise ValueError(msg)

    url = getattr(filing, f'{format_}_url')
    if not url:
        format_text = (
            format_.capitalize() if format_ == 'package' else format_.upper())
        msg = f'{format_text} not available for {filing!r}'
        warnings.warn(msg, FileNotAvailableWarning, stacklevel=2)
        return None

    sha256 = None
    if check_corruption and format_ == 'package':
        sha256 = filing.package_sha256

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
        obj=filing,
        attr_base=format_,
        stem_pattern=stem_pattern,
        filename=filename,
        sha256=sha256
    )
