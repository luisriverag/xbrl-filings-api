"""Define `SQLiteView` class."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(eq=True, frozen=True)
class SQLiteView:
    """Class which stores SQLite view creation instructions."""

    name: str = field(compare=True)
    """
    Name of the view in database.

    If the view already exists, it will not be overwritten.
    """

    required_tables: Iterable[str] = field(compare=False)
    """
    Table names required for this view.

    The table names are class names of APIResource objects other than
    `Filing` (as it will always be included).
    """

    doc: str = field(compare=False)
    """Textual explanation of the view."""

    sql: str = field(compare=False)
    """SQL ``SELECT`` statement for the view."""
