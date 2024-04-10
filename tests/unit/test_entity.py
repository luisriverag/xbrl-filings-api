"""Define tests for `Entity`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import datetime

import pytest

import xbrl_filings_api as xf
import xbrl_filings_api.options as options
import xbrl_filings_api.request_processor as request_processor


@pytest.fixture
def asml22en_entities_filing(asml22en_entities_response, res_colls):
    """ASML Holding 2022 English AFR filing."""
    page_gen = request_processor.generate_pages(
        filters={'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'},
        limit=1,
        flags=xf.GET_ENTITY,
        res_colls=res_colls
        )
    page: xf.FilingsPage = next(page_gen)
    return next(iter(page.filing_list))


@pytest.fixture
def asml22en_entity(asml22en_entities_filing):
    """Entity of URL mock `asml22en_entities`."""
    filing: xf.Filing = asml22en_entities_filing
    return filing.entity


class TestEntityAsml:
    """Test entity object of ASML 2022 filing."""

    def test_repr(self, asml22en_entity):
        """Test Entity.__repr__ method."""
        e_repr = "Entity(name='ASML Holding N.V.')"
        assert repr(asml22en_entity) == e_repr

    def test_str(self, asml22en_entity):
        """Test Entity.__str__ method."""
        ent: xf.Entity = asml22en_entity
        assert str(ent) == 'ASML Holding N.V. (724500Y6DUVHQD6OXN27)'

    def test_str_no_identifier(self, asml22en_entity):
        """Test Entity.__str__ method when `identifier` is None."""
        ent: xf.Entity = asml22en_entity
        ent.identifier = None
        assert str(ent) == 'ASML Holding N.V.'

    def test_str_no_name(self, asml22en_entity):
        """Test Entity.__str__ method when `name` is None."""
        ent: xf.Entity = asml22en_entity
        ent.name = None
        assert str(ent) == '724500Y6DUVHQD6OXN27'

    def test_str_no_identifier_nor_name(self, asml22en_entity):
        """
        Test Entity.__str__ method when `identifier` and `name` are
        None.
        """
        ent: xf.Entity = asml22en_entity
        ent.name = None
        ent.identifier = None
        assert str(ent) == ''

    @pytest.mark.parametrize(('attr_name', 'expected'), [
        ('api_id', '1969'),
        ('identifier', '724500Y6DUVHQD6OXN27'),
        ('name', 'ASML Holding N.V.'),
        ])
    def test_data_attributes(self, asml22en_entity, attr_name, expected):
        """Test non-derived data attributes for Entity."""
        assert getattr(asml22en_entity, attr_name) == expected

    def test_url_data_attributes(self, asml22en_entity, monkeypatch):
        """Test attribute `api_entity_filings_url` for Entity."""
        monkeypatch.setattr(
            options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        e_url = (
            'https://filings.xbrl.org/api/entities/724500Y6DUVHQD6OXN27/filings'
            )
        ent: xf.Entity = asml22en_entity
        assert ent.api_entity_filings_url == e_url

    def test_other_attributes(self, asml22en_entity):
        """Test the meta and object reference attributes for Entity."""
        assert isinstance(asml22en_entity.filings, set)
        for filing in asml22en_entity.filings:
            assert isinstance(filing, xf.Filing)
        assert isinstance(asml22en_entity.query_time, datetime)
        assert isinstance(asml22en_entity.request_url, str)
        assert '://' in asml22en_entity.request_url
