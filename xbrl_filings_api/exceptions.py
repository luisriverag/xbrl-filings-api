"""
The exceptions for the library.

Exception `APIError` is defined separately in module `api_error`.

All of the exceptions are subclasses of `FilingsAPIError or
`FilingsAPIWarning`. This includes `APIError`.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT


class FilingsAPIError(Exception):
    """
    Base class for exceptions in this library.

    Not to be confused with `APIError` which is a subclass of this class
    representing an error returned by JSON:API.
    """


class FilingsAPIWarning(Warning):
    """Base class for warnings in this library."""


class HTTPStatusError(FilingsAPIError):
    """
    The API returns no errors and the HTTP status is other than 200.

    Attributes
    ----------
    status_code : int
    status_text : str
    body : str
    """

    def __init__(self, status_code: int, status_text: str, body: str) -> None:
        """Initialize `HTTPStatusError`."""
        self.status_code = status_code
        """HTTP status code."""
        self.status_text = status_text
        """Description of the HTTP status."""
        self.body = body
        """Body text of the response."""
        super().__init__()


class CorruptDownloadError(FilingsAPIError):
    """
    SHA-256 hash of the downloaded file does not match value from API.

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
        """Initialize `CorruptDownloadError`."""
        self.path = path
        """Path where the file was saved."""
        self.url = url
        """URL where the file was downloaded from."""
        self.calculated_hash = calculated_hash
        """Actual SHA-256 hash of the file in lowercase hex."""
        self.expected_hash = expected_hash
        """Expected SHA-256 hash of the file in lowercase hex."""
        super().__init__()


class DatabaseFileExistsError(FilingsAPIError):
    """
    The intended save path for the database is an existing file.

    Set parameter `update` to `True` to update an existing database.

    Attributes
    ----------
    path : str
    """

    def __init__(self, path: str):
        self.path = path
        """Intended save path for the file."""
        super().__init__()


class DatabasePathIsReservedError(FilingsAPIError):
    """
    The intended save path for the database is already reserved.

    Attributes
    ----------
    path : str
    """

    def __init__(self, path: str):
        self.path = path
        """Intended save path for the file."""
        super().__init__()


class DatabaseSchemaUnmatchError(FilingsAPIError):
    """
    The file contains a database whose schema is non-conformant.

    Either none of the expected tables are present or none of the
    expected columns for a matching table.

    Attributes
    ----------
    path : str
    """

    def __init__(self, path: str):
        self.path = path
        """Path for the database file."""
        super().__init__()


class FilterNotSupportedWarning(FilingsAPIWarning):
    """Used filter is not supported but can be used."""
