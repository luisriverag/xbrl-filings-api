"""Module for download stats counters."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

__all__ = [
    'byte_counter',
    'item_counter',
    ]


byte_counter = 0
"""
Number of bytes downloaded.

Counter starts when the package is imported for the first time.
"""

item_counter = 0
"""
Count of finished file downloads.

Counter starts when the package is imported for the first time.
"""
