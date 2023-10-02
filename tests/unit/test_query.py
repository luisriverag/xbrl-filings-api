"""Define tests for query functions."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import os
import sqlite3
from datetime import datetime, timezone

import pytest
import requests

from xbrl_filings_api import (
    GET_ENTITY,
    GET_ONLY_FILINGS,
    GET_VALIDATION_MESSAGES,
    Entity,
    Filing,
    FilingsPage,
    ValidationMessage,
    options,
    query,
)

UTC = timezone.utc


class TestFundamentalOperation:
    """Test fundamental operation."""

    def test_get_filings(s, asml22en_response):
        """Requested filing is returned."""
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
        assert isinstance(asml22, Filing), 'Filing is returned'

    @pytest.mark.sqlite
    def test_to_sqlite(s, asml22en_response, tmp_path):
        """Requested filing is inserted into a database."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        tmp_db = tmp_path / 'temp.db'
        query.to_sqlite(
            path=tmp_db,
            update=False,
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert os.access(tmp_db, os.F_OK), 'Database file is created'
        con = sqlite3.connect(tmp_db)
        cur = con.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM Filing "
            "WHERE filing_index = ?"
            (asml22_fxo,))
        assert cur.fetchone() == (1,), 'Fetched record ends up in the database'

    @pytest.mark.iter
    def test_filing_page_iter(s, asml22en_response):
        """Requested filing is returned on a filing page."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        piter = query.filing_page_iter(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        page = next(piter, None)
        assert isinstance(page, FilingsPage), 'First iteration returns a page'
        asml22 = next(iter(page.filing_list), None)
        assert isinstance(asml22, Filing), 'Filing is returned'


class TestParam_filters_single:
    """Test parameter `filters` using single filters."""

    def test_get_filings_filing_index(s, asml22en_response):
        """Requested filing index is returned."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        fs = query.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=1,
            flags=GET_ONLY_FILINGS
            )
        assert len(fs) == 1, 'One filing is returned'
        asml22 = next(iter(fs), None)
        assert asml22.filing_index == asml22_fxo

    def test_2_filters_country_enddate(s, finnish_jan22_response):
        """Filters `country` and `last_end_date` return 2 ."""
        fs = query.get_filings(
            filters={
                'country': 'FI',
                'last_end_date': '2022-01-31'
                },
            sort=None,
            max_size=2,
            flags=GET_ONLY_FILINGS
            )
        assert len(fs) == 2, 'Two reports issued in Finland for Jan 2022.'
        fxo_set = {filing.filing_index for filing in fs}
        puuilo22_fxo = '743700UJUT6FWHBXPR69-2022-01-31-ESEF-FI-0'
        assert puuilo22_fxo in fxo_set, 'Puuilo Oyj 2022-01-31'
        hlre22_fxo = '743700UNWAM0XWPHXP50-2022-01-31-ESEF-FI-0'
        assert hlre22_fxo in fxo_set, 'HLRE Holding Oyj 2022-01-31'

    # to_sqlite
    # filing_page_iter


class TestParam_filters_multifilters:
    """Test parameter `filters` using multifilters."""


    # to_sqlite
    # filing_page_iter


class TestParam_filters_short_dates:
    """Test parameter `filters` using date filters."""


    # to_sqlite
    # filing_page_iter


class TestParam_sort:
    """Test parameter `sort`."""

    def test_sort_oldest_finnish_str(s, oldest3_fi_response, monkeypatch):
        """Test sorting by `added_time` str for filings from Finland."""
        monkeypatch.setattr(options, 'utc_time', True)
        fs = query.get_filings(
            filters={
                'country': 'FI'
                },
            sort='added_time',
            max_size=3,
            flags=GET_ONLY_FILINGS
            )
        date_max = datetime(2021, 5, 18, 0, 0, 1, tzinfo=UTC)
        for f in fs:
            assert f.added_time < date_max, 'Before 2021-05-18T00:00:01Z'

    def test_sort_oldest_finnish_list(s, oldest3_fi_response, monkeypatch):
        """Sort by `added_time` for filings from Finland."""
        monkeypatch.setattr(options, 'utc_time', True)
        fs = query.get_filings(
            filters={
                'country': 'FI'
                },
            sort=['added_time'],
            max_size=3,
            flags=GET_ONLY_FILINGS
            )
        date_max = datetime(2021, 5, 18, 0, 0, 1, tzinfo=UTC)
        for f in fs:
            assert f.added_time < date_max, 'Before 2021-05-18T00:00:01Z'

    def test_sort_two_fields(s, sort_two_fields_response):
        """
        Test sorting by `added_time` list for filings from Finland.

        .. warning::

            This test is volatile regarding `mock_upgrade.py` runs.
            Systematically ancient (erraneous?) fact dates in new issued
            filings or introduction of older reports using other
            accounting principles/XBRL taxonomies may break it.
        """
        fs = query.get_filings(
            filters={
                'country': 'FI'
                },
            sort=['last_end_date', 'added_time'],
            max_size=3,
            flags=GET_ONLY_FILINGS
            )
        assert len(fs) == 3, 'Three filings were requested'
        filing_indexes = {f.filing_index for f in fs}
        # TODO: Must be checked from full database output
        oldest_fi_fxo = '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert oldest_fi_fxo in filing_indexes
        _2nd_oldest_fi_fxo = '549300UWB1AIR85BM957-2020-12-31-ESEF-FI-0'
        assert _2nd_oldest_fi_fxo in filing_indexes
        _3rd_oldest_fi_fxo = '7437007N96FK4N3WHT09-2020-12-31-ESEF-FI-0'
        assert _3rd_oldest_fi_fxo in filing_indexes

    # to_sqlite
    # filing_page_iter


class TestParam_max_size:
    """Test parameter `max_size`."""

    # to_sqlite
    # filing_page_iter


class TestParam_flags:
    """Test parameter `flags`."""

    def test_asml22en_flag_only_filings(s, asml22en_response):
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

    def test_asml22en_flag_entities(s, asml22en_entities_response):
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

    def test_asml22en_flag_vmessages(s, asml22en_vmessages_response):
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
        assert isinstance(vmsg.text, str), 'Accessible'

    def test_asml22en_flag_only_filings_and_entities(s, asml22en_response):
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

    # to_sqlite
    # filing_page_iter


class TestParam_add_api_params:
    """Test parameter `add_api_params`."""

    def test_asml22en_override_max_size(s, asml22en_response):
        """`max_size` can be overridden with `add_api_params`."""
        asml22_fxo = '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'
        fs = query.get_filings(
            filters={
                'filing_index': asml22_fxo
                },
            sort=None,
            max_size=10,
            flags=GET_ONLY_FILINGS,
            add_api_params={'page[size]': '1'}
            )
        assert len(fs) == 1, 'Parameter max_size is overridden to be 1'

    # to_sqlite
    # filing_page_iter


class TestParam_paging_single:
    """Test handling of filing pages from the API."""

    @pytest.mark.xfail(
        reason=(
            'Error in undelying API: redundant filings on pages. '
            'Filing with api_id "1" (Cloetta AB, 2021, en) and "2" '
            '(Cloetta AB, 2021, sv) is returned twice and as a result, '
            'a fouth page is requested to fulfil expected 5 filings.'
            ),
        raises=requests.ConnectionError
        )
    def test_filing_page_iter(s, multipage_xfail_response, monkeypatch):
        """Requested filings are available on 3 pages."""
        monkeypatch.setattr(options, 'max_page_size', 2)
        piter = query.filing_page_iter(
            filters={
                'country': 'SE'
                },
            sort='added_time',
            max_size=5,
            flags=GET_ONLY_FILINGS
            )
        page1 = next(piter, None)
        assert isinstance(page1, FilingsPage), 'Pages are returned'
        page2 = next(piter, None)
        assert isinstance(page2, FilingsPage), '3 pages are returned'
        page3 = next(piter, None)
        assert isinstance(page3, FilingsPage), '3 pages are returned'
        page_none = next(piter, None)
        assert page_none is None, 'No more than 3 pages are returned'

    # def test_filing_page_iter_filings_count(s,
            # multipage_response, monkeypatch):
        # """Function returns correct number of filings."""
        # monkeypatch.setattr(options, 'max_page_size', 2)
        # piter = query.filing_page_iter(
            # filters={
                # 'country': 'SE'
                # },
            # sort='added_time',
            # max_size=5,
            # flags=GET_ONLY_FILINGS
            # )
        # for i, page in enumerate(piter):
            # if i < 2:
                # assert len(page.filing_list) == 2, f'Page {i+1} is full with 2 filings'
            # elif i == 2:
                # assert len(page.filing_list) == 1, 'Third page has one filing'
