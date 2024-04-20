"""The exceptions for the pubpackage downloader."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

__all__ = ['CorruptDownloadError']


class CorruptDownloadError(Exception):
    """
    SHA-256 checksum does not match expected value from API.

    This is a different exception than the one in top package
    ``xbrl_filings_api``.
    """

    def __init__(
            self, path: str, url: str, calculated_hash: str,
            expected_hash: str) -> None:
        self.path: str = path
        """Path where the file was saved."""
        self.url: str = url
        """URL where the file was downloaded from."""
        self.calculated_hash: str = calculated_hash
        """Actual SHA-256 checksum of the file in lowercase hex."""
        self.expected_hash: str = expected_hash
        """Expected SHA-256 checksum of the file in lowercase hex."""
        super().__init__()
