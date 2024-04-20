"""Define tests for `debug`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import copy
import re

import pytest
import responses

import xbrl_filings_api as xf
import xbrl_filings_api.debug as xf_debug
from xbrl_filings_api.json_tree import JSONTree

ASML22EN_JSON_BASE = {
    'data': [{
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
                'links': {'related': '/api/filings/4261/validation_messages'}
                },
            'entity': {
                'links': {'related': '/api/entities/724500Y6DUVHQD6OXN27'}
            }
        },
        'id': '4261',
        'links': {'self': '/api/filings/4261'}
        }],
    'links': {
        'self': (
            'https://filings.xbrl.org/api/filings?'
            'page%5Bsize%5D=1&'
            'filter%5Bfxo_id%5D=724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
            )
        },
    'meta': {'count': 1},
    'jsonapi': {'version': '1.0'}
    }


def test_get_unaccessed_key_paths(monkeypatch):
    """
    Test reading newly added data paths in JSON by `debug.get_unaccessed
    key_paths`.
    """
    monkeypatch.setattr(JSONTree, '_unaccessed_paths', {})
    monkeypatch.setattr(JSONTree, '_object_path_counter', {})
    monkeypatch.setattr(JSONTree, 'unexpected_resource_types', set())
    json_with_new_keys = copy.deepcopy(ASML22EN_JSON_BASE)
    json_with_new_keys['data'][0]['attributes']['new_attribute'] = 'new_value'
    json_with_new_keys['data'][0]['relationships']['new_rel'] = {
        'links': {'related': 'new_rel_link'}
        }
    json_with_new_keys['new_root_attribute'] = 'new_root_value'
    e_unaccessed = [
        ('Filing', 'attributes.new_attribute'),
        ('Filing', 'relationships.new_rel.links.related'),
        ('FilingsPage', 'new_root_attribute')
        ]
    with responses.RequestsMock() as rsps:
        rsps.add(
            method='GET',
            url=re.compile(r'.+'),
            json=json_with_new_keys,
        )
        xf.get_filings()
    unaccessed_kpaths = xf_debug.get_unaccessed_key_paths()
    for e_tuple in e_unaccessed:
        for got_tuple in unaccessed_kpaths:
            if got_tuple == e_tuple:
                break
        else:
            pytest.fail(
                f'Did not get unaccessed path (class_qualname={e_tuple[0]!r}, '
                f'key_path={e_tuple[1]!r})'
                )


def test_get_key_path_availability_counts(monkeypatch):
    """
    Test getting read counts for JSON properties by
    `debug.get_key_path_availability_counts`.
    """
    monkeypatch.setattr(JSONTree, '_unaccessed_paths', {})
    monkeypatch.setattr(JSONTree, '_object_path_counter', {})
    monkeypatch.setattr(JSONTree, 'unexpected_resource_types', set())
    with responses.RequestsMock() as rsps:
        rsps.add(
            method='GET',
            url=re.compile(r'.+'),
            json=ASML22EN_JSON_BASE,
        )
        xf.get_filings()
    retrieve_counts = xf_debug.get_key_path_availability_counts()
    data_retrieve = next(filter(
        lambda r: r.class_name == 'FilingsPage' and r.key_path == 'data',
        retrieve_counts))
    assert data_retrieve.success_count == 1
    assert data_retrieve.total_count == 1
    included_retrieve = next(filter(
        lambda r: r.class_name == 'FilingsPage' and r.key_path == 'included',
        retrieve_counts))
    assert included_retrieve.success_count == 0
    assert included_retrieve.total_count == 1
    country_retrieve = next(filter(
        lambda r: (
            r.class_name == 'Filing'
            and r.key_path == 'attributes.country'
            ),
        retrieve_counts))
    assert country_retrieve.success_count == 1
    assert country_retrieve.total_count == 1


def test_get_unexpected_resource_types_data(monkeypatch):
    """
    Test detecting unexpected resource type by
    `debug.get_unexpected_resource_types` from ``data``.
    """
    monkeypatch.setattr(JSONTree, '_unaccessed_paths', {})
    monkeypatch.setattr(JSONTree, '_object_path_counter', {})
    monkeypatch.setattr(JSONTree, 'unexpected_resource_types', set())
    json_with_new_resource_types = copy.deepcopy(ASML22EN_JSON_BASE)
    json_with_new_resource_types['data'].append({
        'type': 'alien_type',
        'id': '123456789',
        'attributes': {},
        'relationships': {},
        'links': {'self': '/api/alien_types/123456789'}
        })
    with responses.RequestsMock() as rsps:
        rsps.add(
            method='GET',
            url=re.compile(r'.+'),
            json=json_with_new_resource_types,
        )
        xf.get_filings()
    unexpected_restypes = xf_debug.get_unexpected_resource_types()
    for type_str, origin in unexpected_restypes:
        if type_str == 'alien_type':
            assert origin == 'data'
            break
    else:
        pytest.fail('Unexpected resource type "alien_type" not detected')


def test_get_unexpected_resource_types_included(monkeypatch):
    """
    Test detecting unexpected resource type by
    `debug.get_unexpected_resource_types` from ``included``.
    """
    monkeypatch.setattr(JSONTree, '_unaccessed_paths', {})
    monkeypatch.setattr(JSONTree, '_object_path_counter', {})
    monkeypatch.setattr(JSONTree, 'unexpected_resource_types', set())
    json_with_new_resource_types = copy.deepcopy(ASML22EN_JSON_BASE)
    json_with_new_resource_types[
        'data'][0]['relationships']['entity']['data'] = {
            'type': 'entity',
            'id': '1969'
            }
    json_with_new_resource_types['included'] = [
        {
            'type': 'entity',
            'id': '1969',
            'attributes': {
                'name': 'ASML Holding N.V.',
                'identifier': '724500Y6DUVHQD6OXN27'
                },
            'relationships': {
                'filings': {
                    'links': {
                        'related': '/api/entities/724500Y6DUVHQD6OXN27/filings'
                        }
                }
            },
            'links': {'self': '/api/entities/724500Y6DUVHQD6OXN27'}
        },
        {
            'type': 'alien_type',
            'id': '123456789',
            'attributes': {},
            'relationships': {},
            'links': {'self': '/api/alien_types/123456789'}
        }
        ]
    with responses.RequestsMock() as rsps:
        rsps.add(
            method='GET',
            url=re.compile(r'.+'),
            json=json_with_new_resource_types,
        )
        fs = xf.get_filings(flags=xf.GET_ENTITY)
        assert isinstance(next(iter(fs)).entity, xf.Entity)
    unexpected_restypes = xf_debug.get_unexpected_resource_types()
    for type_str, origin in unexpected_restypes:
        if type_str == 'alien_type':
            assert origin == 'included'
            break
    else:
        pytest.fail('Unexpected resource type "alien_type" not detected')
