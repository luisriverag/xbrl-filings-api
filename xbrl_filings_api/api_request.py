# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime


@dataclass
class APIRequest:
    url: str
    time: datetime
