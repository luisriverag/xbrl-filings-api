"""Define `APIObject` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Sized
from datetime import datetime

from xbrl_filings_api import options, order_columns
from xbrl_filings_api.api_request import _APIRequest
from xbrl_filings_api.json_tree import _JSONTree
from xbrl_filings_api.time_formats import time_formats


class APIObject:
    """
    Base class for JSON:API objects.

    Attributes
    ----------
    request_time : datetime
    request_url : str
    """

    def __init__(
            self, json_frag: dict, api_request: _APIRequest, *,
            do_not_track: bool = False
            ) -> None:
        self._json = _JSONTree(
            class_name=self.__class__.__qualname__,
            json_frag=json_frag,
            do_not_track=do_not_track
            )
        """
        Timezone-aware datetime when the object was fetched from the
        API.

        This time is equivalent for all objects created in a single API
        function call even if the response contains multiple response
        pages.

        The timezone is chosen according to option `utc_time`.
        """
        self.request_time = api_request.time
        self.request_url = api_request.url

    def __str__(self) -> str:
        """Return string representation of the object."""
        attrs = [
            att for att in dir(self)
            if not (att.startswith('_') or getattr(self.__class__, att, False))
            ]
        attrs = order_columns.order_columns(attrs)
        attvals: list[str] = []
        for att in attrs:
            val_str = None
            val = getattr(self, att)
            if isinstance(val, Sized) and not isinstance(val, str):
                val_str = f'{val.__class__.__qualname__}(len={len(val)})'
            elif isinstance(val, datetime):
                try:
                    fstr = time_formats[options.time_accuracy]
                except KeyError:
                    fstr = time_formats['min']
                val_str = val.strftime(fstr)
            else:
                val_str = repr(val)
            attvals.append(f'{att} = {val_str}')
        attrep = ',\n  '.join(av for av in attvals)
        return f'{__name__}.{self.__class__.__qualname__}(\n  {attrep}\n  )'
