"""Class for stats counters."""


from dataclasses import dataclass


@dataclass
class StatCounters:
    """Global stats counters for downloader package."""

    item_counter = 0
    """Count of finished file downloads after importing the package."""
    byte_counter = 0
    """Number of bytes downloaded after importing the package."""
