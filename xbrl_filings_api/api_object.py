"""Define `APIObject` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.json_tree import _JSONTree


class APIObject:
    """
    Base class for JSON:API objects.

    Attributes
    ----------
    query_time : datetime
    request_url : str
    """

    def __init__(
            self, json_frag: dict, api_request: _APIRequest, *,
            do_not_track: bool = False
            ) -> None:
        """Initialize `APIObject`."""
        if type(self) is APIObject:
            msg = 'APIObject can only be initialized via subclassing'
            raise NotImplementedError(msg)

        self._json = _JSONTree(
            class_name=self.__class__.__qualname__,
            json_frag=json_frag,
            do_not_track=do_not_track
            )
        """Object for traversing and parsing API response."""
        self.query_time = api_request.query_time
        """
        Time when the query function was called.

        The same moment may have multiple different objects with
        different `request_url` values due to paging. This time is not
        the time of receiving the actual request (page) from the API.
        """

        self.request_url = api_request.url
        """URL requested from the API."""
