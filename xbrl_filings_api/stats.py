"""Module for API stats counters."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

page_counter = 0
"""
Count of API page requests received.

A single query may include multiple requests. Counter starts when the
package is imported for the first time.
"""
