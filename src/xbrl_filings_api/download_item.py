# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Mapping, Container
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Optional
import warnings

from .exceptions import FileNotAvailableWarning


@dataclass(frozen=True)
class FullDownloadItem:
    url: str
    to_dir: str | PurePath
    obj: Any
    attr_base: Optional[str] = None
    stem_pattern: Optional[str] = None
    filename: Optional[str] = None
    sha256: Optional[str] = None


@dataclass
class DownloadItem:
    filename: Optional[str] = None
    to_dir: Optional[str | PurePath] = None
    stem_pattern: Optional[str] = None


def construct_download_items(
        formats: str | Iterable[str] | Mapping[str, DownloadItem],
        resource: object,
        to_dir: str | PurePath | None,
        stem_pattern: str | None,
        filename: str | None,
        check_corruption: bool,
        valid_formats: Container
        ) -> list[FullDownloadItem]:
    """Constructs a list of `FullDownloadItem` objects."""
    if isinstance(formats, str):
        formats = [formats]
    items = []

    if isinstance(formats, Mapping):
        for format_key in formats:
            download_item = formats[format_key]
            full_item = _get_full_download_item(
                format_key, download_item, resource, to_dir, stem_pattern,
                filename, check_corruption, valid_formats
                )
            if full_item:
                items.append(full_item)
    
    elif isinstance(formats, Iterable):
        for format in formats:
            full_item = _get_full_download_item(
                format, None, resource, to_dir, stem_pattern, filename,
                check_corruption, valid_formats
                )
            if full_item:
                items.append(full_item)
    else:
        msg = "Parameter 'formats' is neither a Mapping nor an Iterable"
        raise ValueError(msg)
    return items


def _get_full_download_item(
        format: str,
        download_item: DownloadItem | None,
        resource: object,
        to_dir: str | PurePath | None,
        stem_pattern: str | None,
        filename: str | None,
        check_corruption: bool,
        valid_formats: Container
        ) -> FullDownloadItem | None:
    if format not in valid_formats:
        msg = f'Format {format!r} is not among {valid_formats!r}'
        raise ValueError(msg)

    url = getattr(resource, f'{format}_url')
    if not url:
        format_text = (
            format.capitalize() if format == 'package' else format.upper())
        msg = f'{format_text} not available for {resource!r}'
        warnings.warn(msg, FileNotAvailableWarning)
        return None
    
    sha256 = None
    if check_corruption and format == 'package':
        sha256 = resource.package_sha256

    if download_item:
        if download_item.to_dir:
            to_dir = download_item.to_dir
        if download_item.stem_pattern:
            stem_pattern = download_item.stem_pattern
        if download_item.filename:
            filename = download_item.filename
    if not to_dir:
        to_dir = '.'

    return FullDownloadItem(
        url=url,
        to_dir=to_dir,
        obj=resource,
        attr_base=format,
        stem_pattern=stem_pattern,
        filename=filename,
        sha256=sha256
    )
