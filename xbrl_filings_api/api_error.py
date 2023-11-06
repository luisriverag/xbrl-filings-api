"""Define `APIError` classes."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from typing import Union

from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.exceptions import FilingsAPIError


class APIError(FilingsAPIError, APIObject):
    """
    An error from the filings.xbrl.org JSON:API.

    Attributes
    ----------
    title : str or None
    detail : str or None
    code: str or None
    api_status : str or None
    status : int
    status_text : str
    """

    _str_attrs = 'title', 'detail', 'code'

    def __init__(
            self, json_frag: dict, api_request: _APIRequest,
            status: int, status_text: str) -> None:
        """Initiate an error of filings.xbrl.org API."""
        APIObject.__init__(self, json_frag, api_request)

        self.title: Union[str, None] = self._json.get('title')
        """Title of the error."""

        self.detail: Union[str, None] = self._json.get('detail')
        """Details of the error."""

        self.code: Union[str, None] = self._json.get('code')
        """Code of the error."""

        self.api_status: Union[str, None] = self._json.get('status')
        """HTTP status code according to JSON:API reponse."""

        # The following lines may be uncommented if they are taken into
        # use in filing.xbrl.org API.

        # self.api_id: Union[str, None] = self._json.get('id')
        # self.about_url: Union[str, None] = self._json.get(
        #     'links.about', _ParseType.URL)
        # self.source_pointer: Union[str, None] = self._json.get(
        #     'source.pointer')
        # self.source_parameter: Union[str, None] = self._json.get(
        #     'source.parameter')
        # self.meta: Union[str, None] = self._json.get('meta.abc')

        self.status: int = status
        """HTTP status code of the reponse."""

        self.status_text: Union[str, None] = status_text
        """HTTP status code description of the reponse."""

        self._json.close()
        FilingsAPIError.__init__(self)

    def __str__(self) -> str:
        """Return string representation of the error."""
        ats = [f'{att}={getattr(self, att)!r}' for att in self._str_attrs]
        ats_txt = ', '.join(ats)
        return f'{type(self).__qualname__}({ats_txt})'
