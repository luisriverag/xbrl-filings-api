"""
Define tests for `JSONTree`.

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
from xbrl_filings_api.json_tree import JSONTree
from xbrl_filings_api.parse_type import ParseType

UTC = timezone.utc

ASML22EN_ENT_VMSG_FILING_FRAG = {
    'type': 'filing',
    'attributes': {
        'date_added': '2023-02-16 14:33:58.236220',
        'country': 'NL',
        'sha256': (
            '3f44981c656dc2bcd0ed3a88e6d062e6'
            'b8c041a656f420257bccd63535c2b6ac'
            ),
        'report_url': (
            '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en'
            '/reports/asml-2022-12-31-en.xhtml'
            ),
        'fxo_id': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0',
        'error_count': 0,
        'inconsistency_count': 4,
        'viewer_url': (
            '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en'
            '/reports/ixbrlviewer.html'
            ),
        'json_url': (
            '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0'
            '/asml-2022-12-31-en.json'
            ),
        'processed': '2023-04-19 10:20:23.668110',
        'warning_count': 7,
        'period_end': '2022-12-31',
        'package_url': (
            '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0'
            '/asml-2022-12-31-en.zip'
            )
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


@pytest.fixture(scope='module')
def asml22en_ent_vmsg_request_url():
    return (
        'https://filings.xbrl.org/api/filings?page%5Bsize%5D=1&'
        'filter%5Bfxo_id%5D=724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0&'
        'include=entity%2Cvalidation_messages'
        )


@pytest.fixture
def _reset_jsontree_state(monkeypatch):
    """Reset the state of the JSONTree type object."""
    monkeypatch.setattr(JSONTree, '_unaccessed_paths', {})
    monkeypatch.setattr(JSONTree, '_object_path_counter', {})
    monkeypatch.setattr(JSONTree, 'unexpected_resource_types', set())


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_init(asml22en_ent_vmsg_request_url):
    """Test init function."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    assert jtree.class_name == 'Filing'
    assert jtree.tree == ASML22EN_ENT_VMSG_FILING_FRAG
    assert jtree.do_not_track is False
    assert JSONTree.unexpected_resource_types == set()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_close_prematurely(asml22en_ent_vmsg_request_url):
    """Test making a get call after tree has been closed."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    jtree.close()
    with pytest.raises(
            Exception,
            match=r'Cannot call get\(\) when JSONTree has been closed'):
        jtree.get(key_path='attributes.country', parse_type=None)


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_close_twice(asml22en_ent_vmsg_request_url):
    """Test closing the JSONTree twice."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    jtree.close()
    with pytest.raises(
            Exception,
            match=r'Cannot close the same object more than once'):
        jtree.close()


@pytest.mark.date
@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_date_value(asml22en_ent_vmsg_request_url):
    """Test reading a date value from the tree."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    last_end_date = jtree.get(
        key_path='attributes.period_end',
        parse_type=ParseType.DATE
        )
    assert last_end_date == date(2022, 12, 31)
    jtree.close()


@pytest.mark.date
@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_date_value_bad_date(asml22en_ent_vmsg_request_url, caplog):
    """Test reading a bad date value from the tree."""
    caplog.set_level(logging.WARNING)
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['period_end'] = '2022-99-99'
    e_log = (
        "Could not parse ISO date string '2022-99-99' for Filing object JSON "
        "fragment dot access path 'attributes.period_end'."
        )
    jtree = JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    last_end_date = jtree.get(
        key_path='attributes.period_end',
        parse_type=ParseType.DATE
        )
    assert last_end_date is None
    assert e_log in caplog.text
    jtree.close()


@pytest.mark.date
@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_date_value_unparsed(asml22en_ent_vmsg_request_url):
    """Test reading a date value from the tree unparsed."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    last_end_date = jtree.get(
        key_path='attributes.period_end',
        parse_type=None
        )
    assert last_end_date == '2022-12-31'
    jtree.close()


@pytest.mark.datetime
@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_datetime_value(asml22en_ent_vmsg_request_url):
    """Test reading a datetime value from the tree."""
    e_datetime = datetime(2023, 4, 19, 10, 20, 23, 668110, tzinfo=UTC)
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=ParseType.DATETIME
        )
    assert processed_time == e_datetime
    assert processed_time.tzinfo == UTC
    jtree.close()


@pytest.mark.datetime
@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_datetime_value_bad_datetime(
        asml22en_ent_vmsg_request_url, caplog):
    """Test reading a bad datetime value from the tree."""
    caplog.set_level(logging.WARNING)
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['processed'] = '2023-99-99 99:99:99.999999'
    e_log = (
        "Could not parse ISO datetime string '2023-99-99 99:99:99.999999' for "
        "Filing object JSON fragment dot access path 'attributes.processed'."
        )
    jtree = JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=ParseType.DATETIME
        )
    assert processed_time is None
    assert e_log in caplog.text
    jtree.close()


@pytest.mark.datetime
@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_datetime_timezone0200_value(asml22en_ent_vmsg_request_url):
    """Test reading a timezoned (0200) datetime value from the tree."""
    e_datetime = datetime(2023, 4, 19, 8, 20, 23, 668110, tzinfo=UTC)
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['processed'] = '2023-04-19 10:20:23.668110+0200'
    jtree = JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=ParseType.DATETIME
        )
    # 2 hours less in UTC
    assert processed_time == e_datetime
    assert processed_time.tzinfo == timezone(timedelta(seconds=7200))
    jtree.close()


@pytest.mark.datetime
@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_datetime_value_unparsed(asml22en_ent_vmsg_request_url):
    """Test reading a datetime value from the tree unparsed."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    processed_time = jtree.get(
        key_path='attributes.processed',
        parse_type=None
        )
    assert processed_time == '2023-04-19 10:20:23.668110'
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_url_value(asml22en_ent_vmsg_request_url, monkeypatch):
    """Test reading a URL value from the tree."""
    monkeypatch.setattr(
        options, 'entry_point_url', 'https://filings.xbrl.org/api')
    e_url = (
        'https://filings.xbrl.org/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0'
        '/asml-2022-12-31-en/reports/ixbrlviewer.html'
        )
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.viewer_url',
        parse_type=ParseType.URL
        )
    assert viewer_url == e_url
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_url_value_bad_url(asml22en_ent_vmsg_request_url, monkeypatch, caplog):
    """Test reading a bad URL value from the tree."""
    monkeypatch.setattr(
        options, 'entry_point_url', 'https://filings.xbrl.org/api')
    caplog.set_level(logging.WARNING)
    filing_frag = copy.deepcopy(ASML22EN_ENT_VMSG_FILING_FRAG)
    filing_frag['attributes']['viewer_url'] = 'http://[1:2:3:4:5:6/'
    e_log = (
        "Could not determine absolute URL string from 'http://[1:2:3:4:5:6/' "
        'for Filing object JSON fragment dot access path '
        "'attributes.viewer_url'."
        )
    jtree = JSONTree(
        class_name='Filing',
        json_frag=filing_frag,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.viewer_url',
        parse_type=ParseType.URL
        )
    assert viewer_url is None
    assert e_log in caplog.text
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_url_value_unparsed(asml22en_ent_vmsg_request_url):
    """Test reading a URL value from the tree unparsed."""
    e_url = (
        '/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en/reports'
        '/ixbrlviewer.html'
        )
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.viewer_url',
        parse_type=None
        )
    assert viewer_url == e_url
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_int_value(asml22en_ent_vmsg_request_url):
    """Test reading an int value from the tree."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    inconsistency_count = jtree.get(
        key_path='attributes.inconsistency_count',
        parse_type=None
        )
    assert inconsistency_count == 4
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_int_value_as_url_noop(asml22en_ent_vmsg_request_url):
    """Test reading an int value as an URL (no-op) from the tree."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    inconsistency_count = jtree.get(
        key_path='attributes.inconsistency_count',
        parse_type=ParseType.URL
        )
    assert inconsistency_count == 4
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_dict_value(asml22en_ent_vmsg_request_url):
    """Test reading a subdict value from the tree."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    rel_entity = jtree.get(key_path='relationships.entity', parse_type=None)
    assert isinstance(rel_entity, dict)
    assert rel_entity['data']['type'] == 'entity'
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_get_dict_value_parse_datetime_noop(asml22en_ent_vmsg_request_url):
    """
    Test reading a subdict value from the tree, parse_type=DATETIME
    (no-op).
    """
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    rel_entity = jtree.get(
        key_path='relationships.entity',
        parse_type=ParseType.DATETIME
        )
    assert isinstance(rel_entity, dict)
    assert rel_entity['data']['type'] == 'entity'
    jtree.close()


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_do_not_track_false(asml22en_ent_vmsg_request_url):
    """Test do_not_track=False reading."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=False
        )
    viewer_url = jtree.get(
        key_path='attributes.country',
        parse_type=None
        )
    assert viewer_url == 'NL'
    jtree.close()
    rcounts = JSONTree.get_key_path_availability_counts()
    assert len(rcounts) == 1
    rcount = next(iter(rcounts))
    assert rcount.class_name == 'Filing'
    assert rcount.key_path == 'attributes.country'
    assert rcount.success_count == 1
    assert rcount.total_count == 1
    uakpaths = JSONTree.get_unaccessed_key_paths()
    assert 'attributes.country' not in uakpaths
    assert len(uakpaths) == 20


@pytest.mark.usefixtures('_reset_jsontree_state')
def test_raises_do_not_track_true(asml22en_ent_vmsg_request_url):
    """Test do_not_track=True reading."""
    jtree = JSONTree(
        class_name='Filing',
        json_frag=ASML22EN_ENT_VMSG_FILING_FRAG,
        request_url=asml22en_ent_vmsg_request_url,
        do_not_track=True
        )
    viewer_url = jtree.get(
        key_path='attributes.country',
        parse_type=None
        )
    assert viewer_url == 'NL'
    jtree.close()
    rcounts = JSONTree.get_key_path_availability_counts()
    assert len(rcounts) == 0
    assert JSONTree.get_unaccessed_key_paths() == set()
