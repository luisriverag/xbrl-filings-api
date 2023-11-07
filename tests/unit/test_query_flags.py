"""Define tests for query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

# Allow unnecessary double quotes as file includes SQL statements.
# ruff: noqa: Q000

import os
import sqlite3
from datetime import timezone

import pytest
import requests

from xbrl_filings_api import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    APIError,
    Entity,
    Filing,
    FilingsPage,
    ValidationMessage,
    options,
    query,
)
from xbrl_filings_api.exceptions import FilterNotSupportedWarning

UTC = timezone.utc


def _db_record_count(cur):
    cur.execute("SELECT COUNT(*) FROM Filing")
    return cur.fetchone()[0]


def test_get_filings_flag_only_filings(asml22en_response):
    """Test if function returns the filing according to `flags`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = query.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_ONLY_FILINGS
        )
    asml22 = next(iter(fs), None)
    assert asml22.entity is None, 'No entities'
    assert asml22.validation_messages is None, 'No messages'


def test_get_filings_flag_entities(asml22en_entities_response):
    """Test if function returns the filing with `entity`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = query.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_ENTITY
        )
    asml22 = next(iter(fs), None)
    assert asml22.validation_messages is None, 'No messages'
    assert isinstance(asml22.entity, Entity), 'Entity is available'
    assert asml22.entity.name == 'ASML Holding N.V.', 'Accessible'


def test_get_filings_flag_vmessages(asml22en_vmessages_response):
    """Function returns the filing with `validation_messages`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = query.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_VALIDATION_MESSAGES
        )
    asml22 = next(iter(fs), None)
    assert asml22.entity is None, 'No entity'
    vmsg = next(iter(asml22.validation_messages), None)
    assert isinstance(vmsg, ValidationMessage), 'Messages available'
    assert isinstance(vmsg.text, str), 'Messages accessible'


def test_get_filings_flag_only_filings_and_entities(asml22en_response):
    """`GET_ONLY_FILINGS` is stronger than `GET_ENTITY`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = query.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_ONLY_FILINGS | GET_ENTITY
        )
    asml22 = next(iter(fs), None)
    assert asml22.entity is None, 'No entities'
    assert asml22.validation_messages is None, 'No messages'


def test_get_filings_flag_entities_vmessages(asml22en_ent_vmsg_response):
    """Get entities and validation messages."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = query.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        max_size=1,
        flags=GET_ENTITY | GET_VALIDATION_MESSAGES
        )
    asml22 = next(iter(fs), None)
    assert isinstance(asml22.entity, Entity), 'Entity available'
    vmsg = next(iter(asml22.validation_messages), None)
    assert isinstance(vmsg, ValidationMessage), 'Messages available'
    assert isinstance(vmsg.text, str), 'Messages accessible'


# to_sqlite
# filing_page_iter
