"""Define tests for flags of query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import xbrl_filings_api as xf


def test_get_filings_flag_only_filings(asml22en_response):
    """Test if function returns the filing according to `flags`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS
        )
    asml22 = next(iter(fs), None)
    assert asml22.entity is None, 'No entities'
    assert asml22.validation_messages is None, 'No messages'


def test_get_filings_flag_entities(asml22en_entities_response):
    """Test if function returns the filing with `entity`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        limit=1,
        flags=xf.GET_ENTITY
        )
    asml22 = next(iter(fs), None)
    assert asml22.validation_messages is None, 'No messages'
    assert isinstance(asml22.entity, xf.Entity), 'xf.Entity is available'
    assert asml22.entity.name == 'ASML Holding N.V.', 'Accessible'


def test_get_filings_flag_vmessages(asml22en_vmessages_response):
    """Function returns the filing with `validation_messages`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        limit=1,
        flags=xf.GET_VALIDATION_MESSAGES
        )
    asml22 = next(iter(fs), None)
    assert asml22.entity is None, 'No entity'
    vmsg = next(iter(asml22.validation_messages), None)
    assert isinstance(vmsg, xf.ValidationMessage), 'Messages available'
    assert isinstance(vmsg.text, str), 'Messages accessible'


def test_get_filings_flag_only_filings_and_entities(asml22en_response):
    """`xf.GET_ONLY_FILINGS` is stronger than `xf.GET_ENTITY`."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        limit=1,
        flags=xf.GET_ONLY_FILINGS | xf.GET_ENTITY
        )
    asml22 = next(iter(fs), None)
    assert asml22.entity is None, 'No entities'
    assert asml22.validation_messages is None, 'No messages'


def test_get_filings_flag_entities_vmessages(asml22en_ent_vmsg_response):
    """Get entities and validation messages."""
    asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
    fs = xf.get_filings(
        filters={
            'filing_index': asml22_fxo
            },
        sort=None,
        limit=1,
        flags=xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES
        )
    asml22 = next(iter(fs), None)
    assert isinstance(asml22.entity, xf.Entity), 'xf.Entity available'
    vmsg = next(iter(asml22.validation_messages), None)
    assert isinstance(vmsg, xf.ValidationMessage), 'Messages available'
    assert isinstance(vmsg.text, str), 'Messages accessible'
