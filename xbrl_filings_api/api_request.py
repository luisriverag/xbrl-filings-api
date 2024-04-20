"""Define dataclass `APIRequest`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime

__all__ = ['APIRequest']


@dataclass
class APIRequest:
    """Dataclass for API query (HTTP request) metadata."""

    url: str
    query_time: datetime
