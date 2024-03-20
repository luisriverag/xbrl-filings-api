"""
Define tests for `_JSONTree`.

Methods `get_unaccessed_key_paths` and
`get_key_path_availability_counts` are in scope of module `test_debug`
with the exception of init attribute `do_not_track`.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import copy
import logging
from datetime import date, datetime, timedelta, timezone

import pytest

import xbrl_filings_api.options as options
from xbrl_filings_api.enums import _ParseType
from xbrl_filings_api.json_tree import _JSONTree

UTC = timezone.utc

ASML22EN_ENT_VMSG_FILING_FRAG = {
    'type': 'filing',
    'attributes': {
        'date_added': '2023-02-16 14:33:58.236220',
        'country': 'NL',
        'sha256': '3f44981c656dc2bcd0ed3a88e6d062e6b8c041a656f420257bccd63535c2b6ac',
        'report_url': '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en/reports/asml-2022-12-31-en.xhtml',
        'fxo_id': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
        'error_count': 0,
        'inconsistency_count': 4,
        'viewer_url': '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en/reports/ixbrlviewer.html',
        'json_url': '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en.json',
        'processed': '2023-04-19 10:20:23.668110',
        'warning_count': 7,
        'period_end': '2022-12-31',
        'package_url': '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en.zip'
        },
    'relationships': {
        'validation_messages': {
            'links': {'related': '/api/filings/4261/validation_messages'},
            'data': [
            {'type': 'validation_message', 'id': '66611'},
            {'type': 'validation_message', 'id': '66612'},
            {'type': 'validation_message', 'id': '66613'},
            {'type': 'validation_message', 'id': '66614'},
            {'type': 'validation_message', 'id': '66615'},
            {'type': 'validation_message', 'id': '66616'},
            {'type': 'validation_message', 'id': '66617'},
            {'type': 'validation_message', 'id': '66618'},
            {'type': 'validation_message', 'id': '66619'},
            {'type': 'validation_message', 'id': '66620'},
            {'type': 'validation_message', 'id': '66621'}
            ]
            },
        'entity': {
            'links': {'related': '/api/entities/724500Y6DUVHQD6OXN27'},
            'data': {'type': 'entity', 'id': '1969'}
            }
        },
    'id': '4261',
    'links': {'self': '/api/filings/4261'}
    }

@pytest.fixture
def reset_jsontree_state(monkeypatch):
    """Reset the state of the _JSONTree type object."""
    monkeypatch.setattr(_JSONTree, '_unaccessed_paths', {})
    monkeypatch.setattr(_JSONTree, '_object_path_counter', {})
    monkeypatch.setattr(_JSONTree, 'unexpected_resource_types', set())


def test_init(reset_jsontree_state):
    """Test init function."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    assert jtree.class_name == 'Filing'
    assert jtree.tree == ASML22EN_ENT_VMSG_FILING_FRAG
    assert jtree.do_not_track is False
    assert _JSONTree.unexpected_resource_types == set()


def test_close_prematurely(reset_jsontree_state):
    """Test making a get call after tree has been closed."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    jtree.close()
    with pytest.raises(
            Exception,
            match=r'Cannot call get\(\) when _JSONTree has been closed'):
        jtree.get(key_path='attributes.country', parse_type=None)


def test_close_twice(reset_jsontree_state):
    """Test closing the _JSONTree twice."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    jtree.close()
    with pytest.raises(
            Exception,
            match=r'Cannot close the same object more than once'):
        jtree.close()


@pytest.mark.date
def test_get_date_value(reset_jsontree_state):
    """Test reading a date value from the tree."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    last_end_date = jtree.get(
        key_path='attributes.period_end',
        parse_type=_ParseType.DATE
        )
    assert last_end_date == date(2022, 12, 31)
    jtree.close()


@pytest.mark.date
def test_get_date_value_bad_date(reset_jsontree_state, caplog):
    """Test reading a bad date value from the tree."""
    caplog.set_level(logging.WARNING)
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['period_end'] = '2022-99-99'
    e_log = (
        "Could not parse ISO date string '2022-99-99' for Filing object JSON "
        "fragment path 'attributes.period_end'."
        )
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        do_not_track=False
        )
    last_end_date = jtree.get(
        key_path='attributes.period_end',
        parse_type=_ParseType.DATE
        )
    assert last_end_date is None
    assert e_log in caplog.text
    jtree.close()


@pytest.mark.date
def test_get_date_value_unparsed(reset_jsontree_state):
    """Test reading a date value from the tree unparsed."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    last_end_date = jtree.get(
        key_path='attributes.period_end',
        parse_type=None
        )
    assert last_end_date == '2022-12-31'
    jtree.close()


@pytest.mark.datetime
def test_get_datetime_value(reset_jsontree_state):
    """Test reading a datetime value from the tree."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=_ParseType.DATETIME
        )
    assert processed_time == datetime(2023, 4, 19, 10, 20, 23, 668110, tzinfo=UTC)
    assert processed_time.tzinfo == UTC
    jtree.close()


@pytest.mark.datetime
def test_get_datetime_value_bad_datetime(reset_jsontree_state, caplog):
    """Test reading a bad datetime value from the tree."""
    caplog.set_level(logging.WARNING)
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['processed'] = '2023-99-99 99:99:99.999999'
    e_log = (
        "Could not parse ISO datetime string '2023-99-99 99:99:99.999999' for "
        "Filing object JSON fragment path 'attributes.processed'."
        )
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=_ParseType.DATETIME
        )
    assert processed_time is None
    assert e_log in caplog.text
    jtree.close()


@pytest.mark.datetime
def test_get_datetime_timezone0200_value(reset_jsontree_state):
    """Test reading a datetime value from the tree."""
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['processed'] = '2023-04-19 10:20:23.668110+0200'
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=_ParseType.DATETIME
        )
    # 2 hours less in UTC
    assert processed_time == datetime(2023, 4, 19, 8, 20, 23, 668110, tzinfo=UTC)
    assert processed_time.tzinfo == timezone(timedelta(seconds=7200))
    jtree.close()


@pytest.mark.datetime
def test_get_datetime_value_unparsed(reset_jsontree_state):
    """Test reading a datetime value from the tree unparsed."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=None
        )
    assert processed_time == '2023-04-19 10:20:23.668110'
    jtree.close()


def test_get_url_value(reset_jsontree_state, monkeypatch):
    """Test reading a URL value from the tree."""
    monkeypatch.setattr(options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.viewer_url',
        parse_type=_ParseType.URL
        )
    assert viewer_url == (
        'https://filings.xbrl.org/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en/reports/ixbrlviewer.html')
    jtree.close()


def test_get_url_value_bad_url(reset_jsontree_state, monkeypatch, caplog):
    """Test reading a bad URL value from the tree."""
    monkeypatch.setattr(options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
    caplog.set_level(logging.WARNING)
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['viewer_url'] = 'http://[1:2:3:4:5:6/'
    e_log = (
        "Could not determine absolute URL string from 'http://[1:2:3:4:5:6/' "
        "for Filing object JSON fragment path 'attributes.viewer_url'."
        )
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.viewer_url',
        parse_type=_ParseType.URL
        )
    assert viewer_url is None
    assert e_log in caplog.text
    jtree.close()


def test_get_url_value_unparsed(reset_jsontree_state):
    """Test reading a URL value from the tree unparsed."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.viewer_url',
        parse_type=None
        )
    assert viewer_url == (
        '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en/reports/ixbrlviewer.html')
    jtree.close()


def test_get_int_value(reset_jsontree_state):
    """Test reading an int value from the tree."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    inconsistency_count = jtree.get(
        key_path='attributes.inconsistency_count',
        parse_type=None
        )
    assert inconsistency_count == 4
    jtree.close()


def test_get_int_value_as_url_noop(reset_jsontree_state):
    """Test reading an int value as an URL (no-op) from the tree."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    inconsistency_count = jtree.get(
        key_path='attributes.inconsistency_count',
        parse_type=_ParseType.URL
        )
    assert inconsistency_count == 4
    jtree.close()


def test_get_dict_value(reset_jsontree_state):
    """Test reading a subdict value from the tree."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    rel_entity = jtree.get(key_path='relationships.entity', parse_type=None)
    assert isinstance(rel_entity, dict)
    assert rel_entity['data']['type'] == 'entity'
    jtree.close()


def test_get_dict_value_parse_datetime_noop(reset_jsontree_state):
    """Test reading a subdict value from the tree, parse_type=DATETIME (no-op)."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    rel_entity = jtree.get(
        key_path='relationships.entity',
        parse_type=_ParseType.DATETIME
        )
    assert isinstance(rel_entity, dict)
    assert rel_entity['data']['type'] == 'entity'
    jtree.close()


def test_do_not_track_false(reset_jsontree_state):
    """Test do_not_track=False reading."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.country',
        parse_type=None
        )
    assert viewer_url == 'NL'
    jtree.close()
    rcounts = _JSONTree.get_key_path_availability_counts()
    assert len(rcounts) == 1
    rcount = next(iter(rcounts))
    assert rcount.class_name == 'Filing'
    assert rcount.key_path == 'attributes.country'
    assert rcount.success_count == 1
    assert rcount.total_count == 1
    uakpaths = _JSONTree.get_unaccessed_key_paths()
    assert 'attributes.country' not in uakpaths
    assert len(uakpaths) == 20

def test_raises_do_not_track_true(reset_jsontree_state):
    """Test do_not_track=True reading."""
    jtree = _JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        do_not_track=True
        )
    viewer_url = jtree.get(
        key_path='attributes.country',
        parse_type=None
        )
    assert viewer_url == 'NL'
    jtree.close()
    rcounts = _JSONTree.get_key_path_availability_counts()
    assert len(rcounts) == 0
    assert _JSONTree.get_unaccessed_key_paths() == set()
