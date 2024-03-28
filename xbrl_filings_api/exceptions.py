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

    def __str__(self) -> str:
        """Return error as text."""
        parts = []
        msg = getattr(self, 'msg', None)
        if msg:
            parts.append(msg)
        attrlist = []
        for attr_name in dir(self):
            if not (attr_name == 'msg'
                    or attr_name.startswith('_')
                    or getattr(Exception, attr_name, False)):
                val = getattr(self, attr_name)
                if attr_name != 'body':
                    attrlist.append(f'{attr_name}={val!r}')
                else:
                    attrlist.append(f'len(body)={len(val)}')
        attrstr = ', '.join(attrlist)
        if attrstr:
            parts.append(attrstr)
        return ' '.join(parts)


class FilingsAPIWarning(UserWarning):
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


class JSONAPIFormatError(FilingsAPIError):
    """
    The API returns a JSON:API document in bad format.

    Attributes
    ----------
    msg : str
    """

    def __init__(self, msg: str) -> None:
        """Initialize `JSONAPIFormatError`."""
        self.msg = msg
        """Error message."""
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
        """
        Expected SHA-256 hash of the file in lowercase hex.

        Originates from `Filing` attribute `package_sha256`.
        """
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
