"""
Define tests for `Filing`.

Tests for downloading methods are in separate test module
`test_downloading`.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import responses

import xbrl_filings_api as xf
import xbrl_filings_api.options as options
import xbrl_filings_api.request_processor as request_processor

UTC = timezone.utc
MOCK_RESPONSE_PATH = Path(__file__).parent.parent / 'mock_responses'


@pytest.fixture(scope='module')
def get_asml22en_filing():
    """ASML Holding 2022 English AFR filing."""
    def _get_asml22en_filing():
        filing = None
        with responses.RequestsMock() as rsps:
            rsps._add_from_file(MOCK_RESPONSE_PATH / 'asml22en.yaml')
            fs = xf.get_filings(
                filters={'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'},
                sort=None,
                max_size=1,
                flags=xf.GET_ONLY_FILINGS,
                add_api_params=None
                )
            filing = next(iter(fs))
        return filing
    return _get_asml22en_filing


@pytest.fixture
def asml22en_entities_filing(asml22en_entities_response, res_colls):
    """ASML Holding 2022 English AFR filing."""
    page_gen = request_processor.generate_pages(
        filters={'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'},
        max_size=1,
        flags=xf.GET_ENTITY,
        res_colls=res_colls
        )
    page: xf.FilingsPage = next(page_gen)
    return next(iter(page.filing_list))


@pytest.fixture(scope='module')
def get_creditsuisse21en_entity_filing():
    """Credit Suisse 2021 English AFR filing with Entity."""
    def _get_creditsuisse21en_entity_filing():
        filing = None
        with responses.RequestsMock() as rsps:
            rsps._add_from_file(
                MOCK_RESPONSE_PATH / 'creditsuisse21en_by_id_entity.yaml')
            fs = xf.get_filings(
                filters={'api_id': '162'},
                sort=None,
                max_size=1,
                flags=xf.GET_ENTITY,
                add_api_params=None
                )
            filing = next(iter(fs))
        return filing
    return _get_creditsuisse21en_entity_filing


@pytest.fixture
def entity_list():
    """Made-up entity list: companies A, B and C (id 1-3)."""
    req = request_processor._APIRequest(
        'https://filings.xbrl.org/api/filings',
        datetime.now(tz=UTC)
        )
    ent_list = [
        xf.Entity({
            'type': 'entity',
            'id': str(num),
            'attributes': {
                'name': f'Company {chr(64+num)}',
                'identifier': str(num)
                },
            'relationships': {
                'filings': {'links': {'related':
                    f'/api/entities/{num}/filings'
                }}},
            'links': {'self': f'/api/entities/{num}'}
            },
            req
            )
        for num in range(1, 4)
        ]
    return ent_list


@pytest.fixture
def vmessage_list():
    """Made-up validation message list: codes A, B and C (id 1-3)."""
    req = request_processor._APIRequest(
        'https://filings.xbrl.org/api/filings',
        datetime.now(tz=UTC)
        )
    ent_list = [
        xf.ValidationMessage({
            'type': 'validation_message',
            'attributes': {
                'message': 'message',
                'severity': 'WARNING',
                'code': chr(64+num)
                },
            'id': str(num)
            },
            req
            )
        for num in range(1, 4)
        ]
    return ent_list


class TestFilingAsml22enNoEntity:
    """Test ASML 2022 filing in English as Filing object."""

    def test_repr(self, get_asml22en_filing):
        """Test __repr__ method."""
        e_repr = (
            "Filing(filing_index='724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0')")
        filing: xf.Filing = get_asml22en_filing()
        assert repr(filing) == e_repr

    def test_str(self, get_asml22en_filing):
        """Test __str__ method."""
        e_str = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0 2022 [en]'
        filing: xf.Filing = get_asml22en_filing()
        assert str(filing) == e_str

    @pytest.mark.parametrize('attr_name,expected', [
        ('json_url', 'https://filings.xbrl.org/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en.json'),
        ('package_url', 'https://filings.xbrl.org/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en.zip'),
        ('viewer_url', 'https://filings.xbrl.org/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en/reports/ixbrlviewer.html'),
        ('xhtml_url', 'https://filings.xbrl.org/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/asml-2022-12-31-en/reports/asml-2022-12-31-en.xhtml'),
        ])
    def test_url_data_attributes(
            self, get_asml22en_filing, attr_name, expected, monkeypatch):
        """Test non-derived data attributes."""
        monkeypatch.setattr(options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        filing: xf.Filing = get_asml22en_filing()
        assert getattr(filing, attr_name) == expected

    @pytest.mark.parametrize('attr_name,expected', [
        pytest.param(
            'last_end_date', date(2022, 12, 31),
            marks=pytest.mark.date),
        pytest.param(
            'added_time', datetime(2023, 2, 16, 14, 33, 58, 236220, tzinfo=UTC),
            marks=pytest.mark.datetime),
        pytest.param(
            'added_time_str', '2023-02-16 14:33:58.236220',
            marks=pytest.mark.datetime),
        pytest.param(
            'processed_time', datetime(2023, 4, 19, 10, 20, 23, 668110, tzinfo=UTC),
            marks=pytest.mark.datetime),
        pytest.param(
            'processed_time_str', '2023-04-19 10:20:23.668110',
            marks=pytest.mark.datetime),
        ])
    def test_date_and_datetime_data_attributes(
            self, get_asml22en_filing, attr_name, expected):
        """Test data attributes which are not URLs, derived or datetimes."""
        filing: xf.Filing = get_asml22en_filing()
        assert getattr(filing, attr_name) == expected

    @pytest.mark.parametrize('attr_name,expected', [
        ('api_id', '4261'),
        ('country', 'NL'),
        ('filing_index', '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'),
        ('error_count', 0),
        ('inconsistency_count', 4),
        ('warning_count', 7),
        ('entity_api_id', None),
        ('json_download_path', None),
        ('package_download_path', None),
        ('xhtml_download_path', None),
        ('package_sha256', '3f44981c656dc2bcd0ed3a88e6d062e6b8c041a656f420257bccd63535c2b6ac'),
        ])
    def test_other_data_attributes(
            self, get_asml22en_filing, attr_name, expected):
        """Test data attributes which are not URLs, derived or datetimes."""
        filing: xf.Filing = get_asml22en_filing()
        assert getattr(filing, attr_name) == expected

    @pytest.mark.parametrize('attr_name,expected', [
        ('language', 'en'),
        pytest.param(
            'reporting_date', date(2022, 12, 31), marks=pytest.mark.date),
        ])
    def test_derived_attributes(
            self, get_asml22en_filing, attr_name, expected):
        """Test derived data attributes."""
        filing: xf.Filing = get_asml22en_filing()
        assert getattr(filing, attr_name) == expected

    def test_other_attributes(self, get_asml22en_filing):
        """Test the meta and object reference attributes."""
        filing: xf.Filing = get_asml22en_filing()
        assert filing.entity is None
        assert filing.validation_messages is None
        assert isinstance(filing.query_time, datetime)
        assert isinstance(filing.request_url, str)
        assert '://' in filing.request_url


class TestFilingAsml22enWithEntity:
    """Test ASML 2022 filing in English as Filing object with entity."""

    def test_repr(self, asml22en_entities_filing):
        """Test __repr__ method."""
        e_repr = (
            "Filing(entity.name='ASML Holding N.V.', "
            "reporting_date=date(2022, 12, 31), language='en')"
            )
        assert repr(asml22en_entities_filing) == e_repr

    def test_str(self, asml22en_entities_filing):
        """Test __str__ method."""
        e_str = 'ASML Holding N.V. 2022 [en]'
        assert str(asml22en_entities_filing) == e_str

    @pytest.mark.parametrize('attr_name,expected', [
        ('filing_index', '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'),
        ('entity_api_id', '1969'),
        ])
    def test_data_attributes(
            self, asml22en_entities_filing, attr_name, expected):
        """Test non-derived data attributes."""
        assert getattr(asml22en_entities_filing, attr_name) == expected

    def test_other_attributes(self, asml22en_entities_filing):
        """Test the meta and object reference attributes."""
        filing: xf.Filing = asml22en_entities_filing
        assert isinstance(filing.entity, xf.Entity)
        assert filing.validation_messages is None


class TestFilingCreditsuisse21enWithEntity:
    """Test Credit Suisse 2021 English AFR filing as Filing object with entity."""

    def test_repr(self, get_creditsuisse21en_entity_filing):
        """Test __repr__ method."""
        e_repr = (
            "Filing(entity.name='CREDIT SUISSE INTERNATIONAL', "
            "reporting_date=date(2021, 12, 31), language=None)"
            )
        filing: xf.Filing = get_creditsuisse21en_entity_filing()
        assert repr(filing) == e_repr

    def test_str(self, get_creditsuisse21en_entity_filing):
        """Test __str__ method."""
        e_str = 'CREDIT SUISSE INTERNATIONAL 2021'
        filing: xf.Filing = get_creditsuisse21en_entity_filing()
        assert str(filing) == e_str

    @pytest.mark.parametrize('attr_name,expected', [
        ('json_url', None),
        ('package_url', 'https://filings.xbrl.org/E58DKGMJYYYJLN8C3868/2021-12-31/ESEF/LU/0/E58DKGMJYYYJLN8C3868-2021-12-31.zip'),
        ('viewer_url', None),
        ('xhtml_url', None),
        ])
    def test_url_data_attributes(
            self, get_creditsuisse21en_entity_filing, attr_name, expected, monkeypatch):
        """Test data attributes which are not URLs or derived."""
        monkeypatch.setattr(options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        filing: xf.Filing = get_creditsuisse21en_entity_filing()
        assert getattr(filing, attr_name) == expected

    @pytest.mark.parametrize('attr_name,expected', [
        pytest.param(
            'processed_time', datetime(2023, 1, 18, 11, 2, 9, 42110, tzinfo=UTC),
            marks=pytest.mark.datetime),
        pytest.param(
            'processed_time_str', '2023-01-18 11:02:09.042110',
            marks=pytest.mark.datetime),
        ('entity_api_id', '123'),
        ])
    def test_other_data_attributes(
            self, get_creditsuisse21en_entity_filing, attr_name, expected):
        """Test data attributes which are not URLs or derived."""
        filing: xf.Filing = get_creditsuisse21en_entity_filing()
        assert getattr(filing, attr_name) == expected

    def test_other_attributes(self, get_creditsuisse21en_entity_filing):
        """Test the meta and object reference attributes."""
        filing: xf.Filing = get_creditsuisse21en_entity_filing()
        assert isinstance(filing.entity, xf.Entity)
        assert filing.validation_messages is None


@pytest.mark.date
@pytest.mark.parametrize('date_obj,expected', [
    (date(2022, 12, 31), '2022'),
    (date(2022, 12, 1), '2022-12-01'),
    (date(2022, 11, 30), 'Nov-2022'),
    (date(2022, 11, 29), '2022-11-29'),
    (date(2022, 1, 1), '2022-01-01'),
    (date(2022, 1, 31), 'Jan-2022'),
    ])
def test_get_simple_filing_date(
        date_obj, expected, get_asml22en_filing):
    """Test method `_get_simple_filing_date` used by `__str__`."""
    filing: xf.Filing = get_asml22en_filing()
    assert filing._get_simple_filing_date(date_obj) == expected


@pytest.mark.parametrize('api_id,expected_name', [
    ('1', 'Company A'),
    ('3', 'Company C'),
    ])
def test_search_entity_success(
        api_id, expected_name, get_asml22en_filing, entity_list):
    """Test method `_search_entity` used by `entity`."""
    filing: xf.Filing = get_asml22en_filing()
    filing.entity_api_id = api_id
    found_entity = filing._search_entity(entity_list, {})
    assert isinstance(found_entity, xf.Entity)
    assert found_entity.name == expected_name


@pytest.mark.parametrize('api_id', [
    None,
    '0',
    '4',
    ])
def test_search_entity_fail(
        api_id, caplog, get_asml22en_filing, entity_list):
    """Test method `test_search_entity_fail` used by `entity` for failures."""
    caplog.set_level(logging.WARNING)
    filing: xf.Filing = get_asml22en_filing()
    filing.entity_api_id = api_id

    found_entity = filing._search_entity(entity_list, {})

    if api_id is None:
        assert 'No entity defined for' in caplog.text
    else:
        assert 'Entity with api_id=' in caplog.text and ' not found' in caplog.text
    assert found_entity is None


def test_search_validation_messages_success(
        monkeypatch, get_asml22en_filing, vmessage_list):
    """Test method `_search_validation_messages` used by `validation_messages`."""
    filing: xf.Filing = get_asml22en_filing()

    def patch_json_get(key_path: Any = '', parse_type: Any = None):
        return [
            {'type': 'validation_message', 'id': '1'},
            {'type': 'validation_message', 'id': '3'},
            ]
    monkeypatch.setattr(filing._json, 'get', patch_json_get, raising=True)

    found_vmessages = filing._search_validation_messages(vmessage_list, {})

    assert isinstance(found_vmessages, set)
    assert len(found_vmessages) == 2
    for vmsg in found_vmessages:
        assert isinstance(vmsg, xf.ValidationMessage)


def test_search_validation_messages_fail(
        caplog, monkeypatch, get_asml22en_filing, vmessage_list):
    """Test method `_search_validation_messages` used by `validation_messages` for failures."""
    caplog.set_level(logging.WARNING)
    filing: xf.Filing = get_asml22en_filing()

    def patch_json_get(key_path: Any = '', parse_type: Any = None):
        return [
            {'type': 'validation_message', 'id': '0'},
            {'type': 'validation_message', 'id': '4'},
            ]
    monkeypatch.setattr(filing._json, 'get', patch_json_get, raising=True)

    found_vmessages = filing._search_validation_messages(vmessage_list, {})

    for aid in ('0', '4'):
        assert f'Validation message with api_id={aid} not found' in caplog.text
    assert found_vmessages == set()


URL_START = 'https://filings.xbrl.org/api/filings/724500Y6DUVHQD6OXN27/2022-12-31/ESEF/NL/0/'
@pytest.mark.parametrize('url,expected', [
    (None, None),
    ('httpsfilings xbrl asml-2022-12-31-en zip', None),
    (' ', None),
    ((URL_START + 'asml-2022-12-31-en.zip'), 'asml-2022-12-31-en'),
    ((URL_START + 'asml-2022-12-31-en'), 'asml-2022-12-31-en'),
    ((URL_START + 'asml/2022-12-31-en'), '2022-12-31-en'),
    ((URL_START + 'asml/'), 'asml'),
    ])
def test_get_url_stem(url, expected, get_asml22en_filing):
    """Test method `_get_url_stem` used by `language` and `reporting_date`."""
    filing: xf.Filing = get_asml22en_filing()
    if expected is None:
        assert filing._get_url_stem(url) is None
    else:
        assert filing._get_url_stem(url) == expected


def test_language_from_xhtml_url(
        fortum23fi_xhtml_language_response, res_colls):
    """Test language derived from `xhtml_url` when not available in `package_url`."""
    fs = xf.get_filings(
        filters={'api_id': '12366'},
        sort=None,
        max_size=1,
        flags=xf.GET_ONLY_FILINGS,
        add_api_params=None
    )
    fortum23fi = next(iter(fs))
    assert fortum23fi.language == 'fi'
