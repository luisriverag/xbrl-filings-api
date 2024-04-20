"""
The exceptions for the library.

All the exceptions are accessible through the package root namespace.

All of the exceptions are subclasses of :class:`FilingsAPIError` or
:class:`FilingsAPIWarning`. This includes :class:`APIError`.

Exception :class:`APIError` is defined separately in module
:mod:`api_error` due to also being a subclass of :class:`APIObject`.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

__all__ = [
    'FilingsAPIError',
    'FilingsAPIWarning',
    'CorruptDownloadError',
    'DatabaseSchemaUnmatchError',
    'HTTPStatusError',
    'JSONAPIFormatError',
    'FilterNotSupportedWarning',
    ]


class FilingsAPIError(Exception):
    r"""
    Base class for exceptions in this library.

    Not to be confused with `APIError` which is a subclass of this class
    representing an error returned by JSON:API.
    """

    def __str__(self) -> str:
        """
        Return "[<``msg``>] [<attr>=<value>] [len(``body``)=<value>]".

        Placeholder ``attr`` refers to any own attribute of the
        exception instance except ``msg`` or ``body``. Placeholder
        ``value`` is always in :func:`repr` format.
        """
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


class CorruptDownloadError(FilingsAPIError):
    """
    SHA-256 checksum does not match expected value from API.

    See Also
    --------
    downloader.CorruptDownloadError : Not FilingsAPIError subclassed.
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
        """
        Expected SHA-256 checksum of the file in lowercase hex.

        Originates from `Filing` attribute `package_sha256`.
        """
        super().__init__()


class DatabaseSchemaUnmatchError(FilingsAPIError):
    """
    The file contains a database whose schema is non-conformant.

    Either none of the expected tables are present or none of the
    expected columns for a matching table.
    """

    def __init__(self, path: str):
        self.path: str = path
        """Path for the database file."""
        super().__init__()


class HTTPStatusError(FilingsAPIError):
    """No APIError but the HTTP status is not 200."""

    def __init__(self, status_code: int, status_text: str, body: str) -> None:
        self.status_code: int = status_code
        """HTTP status code."""
        self.status_text: str = status_text
        """Description of the HTTP status."""
        self.body: str = body
        """Body text of the response."""
        super().__init__()


class JSONAPIFormatError(FilingsAPIError):
    r"""The API returns a JSON:API document in bad format."""

    def __init__(self, msg: str) -> None:
        self.msg: str = msg
        """Error message."""
        super().__init__()


class FilterNotSupportedWarning(FilingsAPIWarning):
    """Used filter is not supported but can be used."""
