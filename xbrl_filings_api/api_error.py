"""Define `APIError` classes."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from typing import Union

from xbrl_filings_api.api_object import APIObject
from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.exceptions import FilingsAPIError

__all__ = ['APIError']


class APIError(FilingsAPIError, APIObject):
    r"""
    Error returned by the JSON:API.

    See Also
    --------
    xbrl_filings_api.exceptions : The module for all other exceptions.
    """

    _str_attrs = 'title', 'detail', 'code'

    def __init__(
            self, json_frag: dict, api_request: APIRequest,
            status: int, status_text: str) -> None:
        APIObject.__init__(self, json_frag, api_request)

        self.title: Union[str, None] = self._json.get('title')
        """Title of the error."""

        self.detail: Union[str, None] = self._json.get('detail')
        """Details of the error."""

        self.code: Union[str, None] = self._json.get('code')
        """Code of the error."""

        self.api_status: Union[str, None] = self._json.get('status')
        r"""HTTP status code according to the JSON document."""

        # The following lines may be uncommented if they are taken into
        # use in filing.xbrl.org API.

        # self.api_id: Union[str, None] = self._json.get('id')
        # self.about_url: Union[str, None] = self._json.get(
        #     'links.about', ParseType.URL)
        # self.source_pointer: Union[str, None] = self._json.get(
        #     'source.pointer')
        # self.source_parameter: Union[str, None] = self._json.get(
        #     'source.parameter')
        # self.meta: Union[str, None] = self._json.get('meta.abc')

        self.status: int = status
        """HTTP status code of the HTTP reponse."""

        self.status_text: Union[str, None] = status_text
        """HTTP status code description of the reponse."""

        self._json.close()
        FilingsAPIError.__init__(self)

    def __repr__(self) -> str:
        """Return repr with `title`, `detail`, and `code`."""
        return (
            f'{type(self).__name__}('
            f'title={self.title!r}, '
            f'detail={self.detail!r}, '
            f'code={self.code!r})'
            )

    def __str__(self) -> str:
        """
        Return "[<`title`> ][ | <`detail`>][ (<`code`>)]".

        If only code is defined, return "Code: <``code``>". If none of
        the three is defined, return empty string.
        """
        pts = []
        if self.title:
            pts.append(str(self.title))
        if self.detail:
            if self.title:
                pts.append('|')
            pts.append(str(self.detail))
        if self.code:
            if len(pts) == 0:
                pts.append(f'Code: {self.code}')
            else:
                pts.append(f'({self.code})')
        pts = [pt.strip() for pt in pts]
        return ' '.join(pts)
