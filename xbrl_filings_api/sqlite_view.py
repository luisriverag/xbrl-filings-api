"""Define `SQLiteView` class."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class SQLiteView:
    """Class which stores SQLite view instructions."""

    name: str
    required_classes: Iterable[str]
    sql: str
