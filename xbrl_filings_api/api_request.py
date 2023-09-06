"""Define dataclass `APIRequest`."""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime


@dataclass
class APIRequest:
    """Metadata on a single request of an API query."""

    url: str
    time: datetime
