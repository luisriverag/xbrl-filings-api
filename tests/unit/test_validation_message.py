"""Define tests for `ValidationMessage`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import datetime

import pytest

import xbrl_filings_api as xf
import xbrl_filings_api.request_processor as request_processor

ASML22EN_CALC_TEXT = (
    'Calculation inconsistent from '
    'ifrs-full:ProfitLossFromOperatingActivities in link role '
    'http://www.asml.com/role/Statementofcomprehensive'
    'incomeprofitorlossbyfunctionofexpenseStatement reported sum '
    '7,043,900,000 computed sum 6,830,200,000 context '
    'i7b009074c59c4f71a2c42ac624464775_D20210101-20211231 unit '
    'i7fea15d1f3474cdda60b5fff2a4cb15c_e88d9918-4a9b-3a03-83ff-'
    '99baed260fc9 unreportedContributingItems ifrs-full:OtherIncome'
    )
ASSICURAZIONI21IT_DUPLICATE_STR_TEXT = (
    'Duplicated facts with different values have been reported for: '
    'ix:nonNumeric, value:Sede legale in Trieste  != piazza Duca degli '
    'Abruzzi, 2 please review selected entries.'
    )
TECNOTREE21FI_DUPLICATE_NUM_TEXT = (
    'Duplicated facts with different values have been reported for: '
    'ix:nonFraction, value:-637000 != -478000 please review selected entries.'
    )


@pytest.fixture
def asml22en_vmessages_filing(asml22en_vmessages_response, res_colls):
    """ASML Holding 2022 English AFR filing."""
    page_gen = request_processor.generate_pages(
        filters={'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'},
        max_size=1,
        flags=xf.GET_VALIDATION_MESSAGES,
        res_colls=res_colls
        )
    page: xf.FilingsPage = next(page_gen)
    return next(iter(page.filing_list))


@pytest.fixture
def asml22en_calc_msg(asml22en_vmessages_filing):
    """Validation message with id '66614' from `asml22en_vmessages`."""
    filing: xf.Filing = asml22en_vmessages_filing
    vmsg: xf.ValidationMessage = next(filter(
        lambda vm: vm.api_id == '66614',
        filing.validation_messages
        ))
    return vmsg


@pytest.fixture
def asml22en_positive_msg(res_colls, asml22en_vmessages_filing):
    """Validation message with id '66615' from `asml22en_vmessages`."""
    filing: xf.Filing = asml22en_vmessages_filing
    vmsg: xf.ValidationMessage = next(filter(
        lambda vm: vm.api_id == '66615',
        filing.validation_messages
        ))
    return vmsg


@pytest.fixture
def assicurazioni21it_vmessages_filing(
        assicurazioni21it_vmessages_response, res_colls):
    """Assicurazioni Generali 2021 Italian AFR filing."""
    page_gen = request_processor.generate_pages(
        filters={'filing_index': '549300X5UKJVE386ZB61-2021-12-31-ESEF-IT-0'},
        max_size=1,
        flags=xf.GET_VALIDATION_MESSAGES,
        res_colls=res_colls
        )
    page: xf.FilingsPage = next(page_gen)
    return next(iter(page.filing_list))


@pytest.fixture
def assicurazioni21it_duplicate_str_msg(assicurazioni21it_vmessages_filing):
    """Validation message with id '104877' from `assicurazioni21it_vmessages`."""
    filing: xf.Filing = assicurazioni21it_vmessages_filing
    vmsg: xf.ValidationMessage = next(filter(
        lambda vm: vm.api_id == '104877',
        filing.validation_messages
        ))
    return vmsg


@pytest.fixture
def tecnotree21fi_vmessages_filing(
        tecnotree21fi_vmessages_response, res_colls):
    """Tecnotree 2021 Finnish AFR filing."""
    page_gen = request_processor.generate_pages(
        filters={'filing_index': '743700MRPVYI7ASHCX38-2021-12-31-ESEF-FI-0'},
        max_size=1,
        flags=xf.GET_VALIDATION_MESSAGES,
        res_colls=res_colls
        )
    page: xf.FilingsPage = next(page_gen)
    return next(iter(page.filing_list))


@pytest.fixture
def tecnotree21fi_duplicate_num_msg(res_colls, tecnotree21fi_vmessages_filing):
    """Validation message with id '41766' from `tecnotree21fi_vmessages`."""
    filing: xf.Filing = tecnotree21fi_vmessages_filing
    vmsg: xf.ValidationMessage = next(filter(
        lambda vm: vm.api_id == '41766',
        filing.validation_messages
        ))
    return vmsg


class TestCalcMsg:
    """Test calcInconsistency code in ASML 2022 filing in English."""

    def test_repr(self, asml22en_calc_msg):
        """Test __repr__ method."""
        e_repr = "ValidationMessage(code='xbrl.5.2.5.2:calcInconsistency')"
        assert repr(asml22en_calc_msg) == e_repr

    def test_str(self, asml22en_calc_msg):
        """Test __str__ method."""
        assert str(asml22en_calc_msg) == ASML22EN_CALC_TEXT

    @pytest.mark.parametrize('attr_name,expected', [
        ('api_id', '66614'),
        ('severity', 'INCONSISTENCY'),
        ('text', ASML22EN_CALC_TEXT),
        ('code', 'xbrl.5.2.5.2:calcInconsistency'),
        ('filing_api_id', '4261'),
        ])
    def test_data_attributes(
            self, asml22en_calc_msg, attr_name, expected):
        """Test non-derived data attributes."""
        assert getattr(asml22en_calc_msg, attr_name) == expected

    @pytest.mark.parametrize('attr_name,expected', [
        ('calc_computed_sum', 6_830_200_000.0),
        ('calc_reported_sum', 7_043_900_000.0),
        ('calc_context_id', 'i7b009074c59c4f71a2c42ac624464775_D20210101-20211231'),
        ('calc_line_item', 'ifrs-full:ProfitLossFromOperatingActivities'),
        ('calc_short_role', 'StatementofcomprehensiveincomeprofitorlossbyfunctionofexpenseStatement'),
        ('calc_unreported_items', ['ifrs-full:OtherIncome']),
        ('duplicate_greater', None),
        ('duplicate_lesser', None),
        ])
    def test_derived_attributes(
            self, asml22en_calc_msg, attr_name, expected):
        """Test derived attributes."""
        if expected is None:
            assert getattr(asml22en_calc_msg, attr_name) is expected
        else:
            assert getattr(asml22en_calc_msg, attr_name) == expected

    def test_other_attributes(self, asml22en_calc_msg):
        """Test the meta and object reference attributes."""
        assert isinstance(asml22en_calc_msg.filing, xf.Filing)
        assert isinstance(asml22en_calc_msg.query_time, datetime)
        assert isinstance(asml22en_calc_msg.request_url, str)
        assert '://' in asml22en_calc_msg.request_url


class TestPositiveMsg:
    """Test 'message:positive' code in ASML 2022 filing in English."""

    def test_repr(self, asml22en_positive_msg):
        """Test __repr__ method."""
        e_repr = "ValidationMessage(code='message:positive')"
        assert repr(asml22en_positive_msg) == e_repr

    def test_str(self, asml22en_positive_msg):
        """Test __str__ method."""
        assert str(asml22en_positive_msg) == 'Reported value is below 0'

    @pytest.mark.parametrize('attr_name,expected', [
        ('api_id', '66615'),
        ('severity', 'WARNING'),
        ('text', 'Reported value is below 0'),
        ('code', 'message:positive'),
        ('filing_api_id', '4261'),
        ])
    def test_data_attributes(
            self, asml22en_positive_msg, attr_name, expected):
        """Test non-derived data attributes."""
        assert getattr(asml22en_positive_msg, attr_name) == expected

    @pytest.mark.parametrize('attr_name', [
        'calc_computed_sum',
        'calc_reported_sum',
        'calc_context_id',
        'calc_line_item',
        'calc_short_role',
        'calc_unreported_items',
        'duplicate_greater',
        'duplicate_lesser',
        ])
    def test_derived_attributes(
            self, asml22en_positive_msg, attr_name):
        """Test derived attributes."""
        assert getattr(asml22en_positive_msg, attr_name) is None

    def test_nondata_attributes(self, asml22en_positive_msg):
        """Test the non-data attributes."""
        assert isinstance(asml22en_positive_msg.filing, xf.Filing)
        assert isinstance(asml22en_positive_msg.query_time, datetime)
        assert isinstance(asml22en_positive_msg.request_url, str)
        assert '://' in asml22en_positive_msg.request_url


class TestDuplicateStrMsg:
    """Test duplicate strings in Assicurazioni 2021 filing in Italian."""

    def test_repr(self, assicurazioni21it_duplicate_str_msg):
        """Test __repr__ method."""
        e_repr = "ValidationMessage(code='message:tech_duplicated_facts1')"
        assert repr(assicurazioni21it_duplicate_str_msg) == e_repr

    def test_str(self, assicurazioni21it_duplicate_str_msg):
        """Test __str__ method."""
        vmsg: xf.ValidationMessage = assicurazioni21it_duplicate_str_msg
        assert str(vmsg) == ASSICURAZIONI21IT_DUPLICATE_STR_TEXT

    @pytest.mark.parametrize('attr_name,expected', [
        ('api_id', '104877'),
        ('severity', 'WARNING'),
        ('text', ASSICURAZIONI21IT_DUPLICATE_STR_TEXT),
        ('code', 'message:tech_duplicated_facts1'),
        ('filing_api_id', '7039'),
        ])
    def test_data_attributes(
            self, assicurazioni21it_duplicate_str_msg, attr_name, expected):
        """Test non-derived data attributes."""
        vmsg: xf.ValidationMessage = assicurazioni21it_duplicate_str_msg
        assert getattr(vmsg, attr_name) == expected

    @pytest.mark.parametrize('attr_name', [
        'calc_computed_sum',
        'calc_reported_sum',
        'calc_context_id',
        'calc_line_item',
        'calc_short_role',
        'calc_unreported_items',
        'duplicate_greater',
        'duplicate_lesser',
        ])
    def test_derived_attributes(
            self, assicurazioni21it_duplicate_str_msg, attr_name):
        """Test derived attributes."""
        assert getattr(assicurazioni21it_duplicate_str_msg, attr_name) is None

    def test_nondata_attributes(self, assicurazioni21it_duplicate_str_msg):
        """Test the non-data attributes."""
        vmsg: xf.ValidationMessage = assicurazioni21it_duplicate_str_msg
        assert isinstance(vmsg.filing, xf.Filing)
        assert isinstance(vmsg.query_time, datetime)
        assert isinstance(vmsg.request_url, str)
        assert '://' in vmsg.request_url


class TestDuplicateNumMsg:
    """Test duplicate numbers in Tecnotree 2021 filing in Finnish."""

    def test_repr(self, tecnotree21fi_duplicate_num_msg):
        """Test __repr__ method."""
        e_repr = "ValidationMessage(code='message:tech_duplicated_facts1')"
        assert repr(tecnotree21fi_duplicate_num_msg) == e_repr

    def test_str(self, tecnotree21fi_duplicate_num_msg):
        """Test __str__ method."""
        vmsg: xf.ValidationMessage = tecnotree21fi_duplicate_num_msg
        assert str(vmsg) == TECNOTREE21FI_DUPLICATE_NUM_TEXT

    @pytest.mark.parametrize('attr_name,expected', [
        ('api_id', '41766'),
        ('severity', 'WARNING'),
        ('text', TECNOTREE21FI_DUPLICATE_NUM_TEXT),
        ('code', 'message:tech_duplicated_facts1'),
        ('filing_api_id', '3965'),
        ])
    def test_data_attributes(
            self, tecnotree21fi_duplicate_num_msg, attr_name, expected):
        """Test non-derived data attributes."""
        assert getattr(tecnotree21fi_duplicate_num_msg, attr_name) == expected

    @pytest.mark.parametrize('attr_name,expected', [
        ('calc_computed_sum', None),
        ('calc_reported_sum', None),
        ('calc_context_id', None),
        ('calc_line_item', None),
        ('calc_short_role', None),
        ('calc_unreported_items', None),
        ('duplicate_greater', -478000),
        ('duplicate_lesser', -637000),
        ])
    def test_derived_attributes(
            self, tecnotree21fi_duplicate_num_msg, attr_name, expected):
        """Test derived attributes."""
        vmsg: xf.ValidationMessage = tecnotree21fi_duplicate_num_msg
        if expected is None:
            assert getattr(vmsg, attr_name) is None
        else:
            assert getattr(vmsg, attr_name) == expected

    def test_nondata_attributes(self, tecnotree21fi_duplicate_num_msg):
        """Test the non-data attributes."""
        vmsg: xf.ValidationMessage = tecnotree21fi_duplicate_num_msg
        assert isinstance(vmsg.filing, xf.Filing)
        assert isinstance(vmsg.query_time, datetime)
        assert isinstance(vmsg.request_url, str)
        assert '://' in vmsg.request_url


def test_str_empty_message(tecnotree21fi_duplicate_num_msg):
    """Test __str__ method."""
    vmsg: xf.ValidationMessage = tecnotree21fi_duplicate_num_msg
    vmsg.text = None
    assert str(vmsg) == ''
