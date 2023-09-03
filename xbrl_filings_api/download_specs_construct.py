"""
Module for constructing download items from Filing and FilingSet objects.

"""


from collections.abc import Iterable, Mapping, Container
from pathlib import PurePath
from typing import Any
import warnings

from .download_item import DownloadItem
from .downloader import DownloadSpecs
from .exceptions import FileNotAvailableWarning


def construct(
        formats: str | Iterable[str] | Mapping[str, DownloadItem],
        filing: Any,
        to_dir: str | PurePath | None,
        stem_pattern: str | None,
        filename: str | None,
        check_corruption: bool,
        valid_formats: Container
        ) -> list[DownloadSpecs]:
    """Constructs a list of `DownloadSpecs` objects."""
    if isinstance(formats, str):
        formats = [formats]
    items = []

    if isinstance(formats, Mapping):
        for format_key in formats:
            download_item = formats[format_key]
            full_item = _get_filing_download_specs(
                format_key, download_item, filing, to_dir, stem_pattern,
                filename, check_corruption, valid_formats
                )
            if full_item:
                items.append(full_item)
    
    elif isinstance(formats, Iterable):
        for format in formats:
            full_item = _get_filing_download_specs(
                format, None, filing, to_dir, stem_pattern, filename,
                check_corruption, valid_formats
                )
            if full_item:
                items.append(full_item)
    else:
        msg = "Parameter 'formats' is neither a Mapping nor an Iterable"
        raise ValueError(msg)
    return items


def _get_filing_download_specs(
        format: str,
        download_item: DownloadItem | None,
        filing: Any,
        to_dir: str | PurePath | None,
        stem_pattern: str | None,
        filename: str | None,
        check_corruption: bool,
        valid_formats: Container
        ) -> DownloadSpecs | None:
    if format not in valid_formats:
        msg = f'Format {format!r} is not among {valid_formats!r}'
        raise ValueError(msg)

    url = getattr(filing, f'{format}_url')
    if not url:
        format_text = (
            format.capitalize() if format == 'package' else format.upper())
        msg = f'{format_text} not available for {filing!r}'
        warnings.warn(msg, FileNotAvailableWarning)
        return None
    
    sha256 = None
    if check_corruption and format == 'package':
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
        attr_base=format,
        stem_pattern=stem_pattern,
        filename=filename,
        sha256=sha256
    )
