"""The exceptions for the pubpackage downloader."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT


class CorruptDownloadError(Exception):
    """
    SHA-256 hash of the downloaded file does not match value from API.

    This is a different exception than the one in
    `xbrl_filings_api.exceptions`.

    Attributes
    ----------
    path : str
    url : str
    calculated_hash : str
    expected_hash : str
    """

    def __init__(
            self, path: str, url: str, calculated_hash: str,
            expected_hash: str) -> None:
        """Initialize `downloader.CorruptDownloadError`."""
        self.path = path
        """Path where the file was saved."""
        self.url = url
        """URL where the file was downloaded from."""
        self.calculated_hash = calculated_hash
        """Actual SHA-256 hash of the file in lowercase hex."""
        self.expected_hash = expected_hash
        """Expected SHA-256 hash of the file in lowercase hex."""
        super().__init__()
