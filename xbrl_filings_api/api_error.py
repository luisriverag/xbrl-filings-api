"""Define `APIError` and `APIErrorGroup` classes."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.exceptions import FilingsAPIError, FilingsAPIErrorGroup


class APIErrorGroup(FilingsAPIErrorGroup):
    """Stores instances of `APIError`."""


class APIError(FilingsAPIError, APIObject):
    """
    The response contains an error from the filings.xbrl.org JSON:API.

    This exception is always raised in a APIErrorGroup.

    Attributes
    ----------
    title : str or None
    detail : str or None
    code: str or None
    api_status : str or None
    status : int
    status_text : str
    """

    _str_attrs = ('title', 'detail', 'code')

    def __init__(
            self, json_frag: dict, api_request: _APIRequest,
            status: int, status_text: str) -> None:
        """Initiate an error of filings.xbrl.org API."""
        APIObject.__init__(self, json_frag, api_request)

        self.title: str | None = self._json.get('title')
        """Title of the error."""

        self.detail: str | None = self._json.get('detail')
        """Details of the error."""

        self.code: str | None = self._json.get('code')
        """Code of the error."""

        self.api_status: str | None = self._json.get('status')
        """HTTP status code according to JSON:API reponse."""

        # The following lines may be uncommented if they are taken into
        # use in filing.xbrl.org API.

        # self.api_id: str | None = self._json.get('id')
        # self.about_url: str | None = self._json.get(
        #     'links.about', _ParseType.URL)
        # self.source_pointer: str | None = self._json.get(
        #     'source.pointer')
        # self.source_parameter: str | None = self._json.get(
        #     'source.parameter')
        # self.meta: str | None = self._json.get('meta.abc')

        self.status: int = status
        """HTTP status code of the reponse."""

        self.status_text: str | None = status_text
        """HTTP status code description of the reponse."""

        self._json.close()
        FilingsAPIError.__init__(self)

    def __str__(self) -> str:
        """Return string representation of the error."""
        ats = [f'{att}={getattr(self, att)!r}' for att in self._str_attrs]
        ats_txt = ', '.join(ats)
        return f'{self.__class__.__qualname__}({ats_txt})'
