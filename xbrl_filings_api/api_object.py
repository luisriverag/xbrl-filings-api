"""Define `APIObject` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from xbrl_filings_api.api_request import APIRequest
from xbrl_filings_api.json_tree import JSONTree

__all__ = ['APIObject']


class APIObject:
    r"""Base class for JSON:API objects."""

    def __init__(
            self, json_frag: dict, api_request: APIRequest, *,
            do_not_track: bool = False
            ) -> None:
        if type(self) is APIObject:
            msg = 'APIObject can only be initialized via subclassing'
            raise NotImplementedError(msg)

        self.query_time: datetime = api_request.query_time
        """
        Time when the query function was called for an `APIObject`.

        The same moment may have multiple different objects with
        different `request_url` values due to paging. This time is not
        the time of receiving the actual request (page) from the API.
        """

        self.request_url: str = api_request.url
        """HTTP request URL for an `APIObject`."""

        self._json = JSONTree(
            class_name=type(self).__qualname__,
            json_frag=json_frag,
            request_url=api_request.url,
            do_not_track=do_not_track
            )
        """Object for traversing and parsing API response."""
