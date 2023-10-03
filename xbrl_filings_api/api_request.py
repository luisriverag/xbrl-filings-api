"""Define dataclass `_APIRequest`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime


@dataclass
class _APIRequest:
    """Metadata on a single request of an API query."""

    url: str
    query_time: datetime
