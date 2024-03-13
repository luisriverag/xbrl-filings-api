"""Define tests for `FilingsPage`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api as xf


@pytest.fixture
def oldest3_fi_ent_vmessages_filingspage(oldest3_fi_ent_vmessages_response):
    """FilingPage for ``oldest3_fi_ent_vmessages`` with entities and validation messages."""
    piter = xf.filing_page_iter(
        filters={'country': 'FI'},
        sort='date_added',
        max_size=3,
        flags=(xf.GET_ENTITY | xf.GET_VALIDATION_MESSAGES),
        add_api_params=None
        )
    return next(piter)


def test_attributes(oldest3_fi_ent_vmessages_filingspage):
    """Test attributes of `FilingsPage`."""
    fpage: xf.FilingsPage = oldest3_fi_ent_vmessages_filingspage
    assert fpage.query_filing_count > 10
    assert len(fpage.filing_list) == 3
    for filing in fpage.filing_list:
        assert isinstance(filing, xf.Filing)
    assert len(fpage.entity_list) == 3
    for ent in fpage.entity_list:
        assert isinstance(ent, xf.Entity)
    assert len(fpage.validation_message_list) > 3
    for vmsg in fpage.validation_message_list:
        assert isinstance(vmsg, xf.ValidationMessage)


def test_repr(oldest3_fi_ent_vmessages_filingspage):
    """Test `__repr__` of `FilingsPage`."""
    e_repr1 = (
        "FilingsPage(request_url='https://filings.xbrl.org/api/filings?")
    e_repr2 = (
        "', query_time=datetime("
        )
    e_repr3 = (
        '), len(filing_list)=3, len(entity_list)=3, '
        'len(validation_message_list)=45)'
        )
    fpage: xf.FilingsPage = oldest3_fi_ent_vmessages_filingspage
    fpage_repr = repr(fpage)
    assert fpage_repr.startswith(e_repr1)
    assert e_repr2 in fpage_repr
    assert fpage_repr.endswith(e_repr3)


# xf.FilingsPage._get_filings
# xf.FilingsPage._parse_filing_fragment
# xf.FilingsPage._get_inc_resource
# xf.FilingsPage._determine_unexpected_inc_resources
# xf.FilingsPage._check_validation_messages_references
