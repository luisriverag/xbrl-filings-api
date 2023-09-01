"""Class for stats counters."""


from dataclasses import dataclass


@dataclass
class StatCounters:
    item_counter = 0
    """Count of executed file downloads after importing the package."""
    byte_counter = 0
    """Number of bytes downloaded after importing the package."""
