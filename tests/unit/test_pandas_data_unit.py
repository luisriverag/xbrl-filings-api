"""
Define unit tests for method `get_pandas_data` of `FilingSet` and
`ResourceCollection`.

Tests with integration test focus are found from module
`integration.test_pandas_data`.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime

import pytest

import xbrl_filings_api as xf


class TestFilingSet_get_pandas_data:
    """Test method FilingSet.get_pandas_data."""

    def test_defaults(self, get_oldest3_fi_filingset):
        """Test default parameter values."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert pd_data['country'][i] == 'FI'
        assert pd_data['filing_index'][i] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert pd_data['language'][i] == 'en'
        assert pd_data['error_count'][i] == 0
        assert pd_data['inconsistency_count'][i] == 19
        assert pd_data['warning_count'][i] == 0
        assert 'added_time_str' not in pd_data
        assert 'processed_time_str' not in pd_data
        assert 'entity_api_id' not in pd_data
        assert 'json_url' not in pd_data
        assert 'package_url' not in pd_data
        assert 'viewer_url' not in pd_data
        assert 'xhtml_url' not in pd_data
        assert 'request_url' not in pd_data
        assert 'json_download_path' not in pd_data
        assert 'package_download_path' not in pd_data
        assert 'xhtml_download_path' not in pd_data
        assert pd_data['package_sha256'][i] == 'ab0c60224c225ba3921188514ecd6c37af6a947f68a5c3a0c6eb34abfaae822b'
        assert 'entity' not in pd_data
        assert 'validation_messages' not in pd_data
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    @pytest.mark.date
    def test_attr_names_3cols(self, get_oldest3_fi_filingset):
        """Test attr_names defining 3 columns."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=['api_id', 'filing_index', 'last_end_date'],
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert len(pd_data) == 3
        assert pd_data['filing_index'][i] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert pd_data['last_end_date'][i] == datetime(2020, 12, 31)
        assert pd_data['last_end_date'][i].tzinfo is None
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    @pytest.mark.date
    def test_attr_names_entity_attr_with_entity_false(
            self, get_oldest3_fi_entities_filingset):
        """Test attr_names with entity attribute, still with_entity=False."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=['api_id', 'filing_index', 'last_end_date', 'entity.name'],
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert len(pd_data) == 4
        assert pd_data['filing_index'][i] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert pd_data['last_end_date'][i] == datetime(2020, 12, 31)
        assert pd_data['last_end_date'][i].tzinfo is None
        assert pd_data['entity.name'][i] == 'Enento Group Oyj'
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    def test_with_entity_true(self, get_oldest3_fi_entities_filingset):
        """Test with_entity=True."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=True,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert pd_data['filing_index'][i] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert 'entity_api_id' not in pd_data
        assert pd_data['entity.api_id'][i] == '548'
        assert pd_data['entity.identifier'][i] == '743700EPLUWXE25HGM03'
        assert pd_data['entity.name'][i] == 'Enento Group Oyj'
        assert 'entity.api_entity_filings_url' not in pd_data
        assert isinstance(pd_data['entity.query_time'][i], datetime)
        assert 'entity.request_url' not in pd_data
        assert 'entity.filings' not in pd_data
        assert 'entity' not in pd_data
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    @pytest.mark.datetime
    def test_strip_timezone_false(self, get_oldest3_fi_filingset):
        """Test strip_timezone=False."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=False,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert pd_data['added_time'][i].tzinfo is not None
        assert pd_data['processed_time'][i].tzinfo is not None
        assert pd_data['query_time'][i].tzinfo is not None
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    @pytest.mark.date
    def test_date_as_datetime_false(self, get_oldest3_fi_filingset):
        """Test date_as_datetime=False."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=False,
            include_urls=False,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert type(pd_data['last_end_date'][i]) is date
        assert type(pd_data['reporting_date'][i]) is date
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    def test_include_urls_true(self, get_oldest3_fi_filingset, monkeypatch):
        """Test include_urls=True."""
        monkeypatch.setattr(xf.options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=True,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert pd_data['json_url'][i] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31 EN.json'
        assert pd_data['package_url'][i] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31_EN.zip'
        assert pd_data['viewer_url'][i] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31_EN/reports/ixbrlviewer.html'
        assert pd_data['xhtml_url'][i] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31_EN/reports/ENENTO-2020-12-31 EN.html'
        assert pd_data['request_url'][i].startswith('https://filings.xbrl.org/api/filings?')
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    def test_with_entity_include_urls_both_true(
            self, get_oldest3_fi_entities_filingset, monkeypatch):
        """Test with_entity=True and include_urls=True."""
        monkeypatch.setattr(xf.options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=True,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=True,
            include_paths=False
            )
        i = pd_data['api_id'].index('710')
        assert 'entity_api_id' not in pd_data
        assert pd_data['entity.api_id'][i] == '548'
        assert pd_data['entity.identifier'][i] == '743700EPLUWXE25HGM03'
        assert pd_data['entity.name'][i] == 'Enento Group Oyj'
        assert pd_data['entity.api_entity_filings_url'][i] == 'https://filings.xbrl.org/api/entities/743700EPLUWXE25HGM03/filings'
        assert isinstance(pd_data['entity.query_time'][i], datetime)
        assert pd_data['entity.request_url'][i].startswith('https://filings.xbrl.org/api/filings?')
        assert 'entity.filings' not in pd_data
        assert 'entity' not in pd_data
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    def test_include_paths_true_has_downloaded(self, get_oldest3_fi_filingset):
        """Test include_paths=True and filings were downloaded."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        enento20en_filing = next(filter(lambda f: f.api_id == '710', fs))
        enento20en_filing.json_download_path = 'test_json'
        enento20en_filing.package_download_path = 'test_package'
        enento20en_filing.xhtml_download_path = 'test_xhtml'
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=True
            )
        i = pd_data['api_id'].index('710')
        assert pd_data['json_download_path'][i] == 'test_json'
        assert pd_data['package_download_path'][i] == 'test_package'
        assert pd_data['xhtml_download_path'][i] == 'test_xhtml'
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    def test_include_paths_true_not_downloaded(self, get_oldest3_fi_filingset):
        """Test include_paths=True but no filings were downloaded."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=True
            )
        assert 'json_download_path' not in pd_data
        assert 'package_download_path' not in pd_data
        assert 'xhtml_download_path' not in pd_data
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']

    def test_include_paths_false_has_downloaded(self, get_oldest3_fi_filingset):
        """Test include_paths=False and filings were downloaded."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        enento20en_filing = next(filter(lambda f: f.api_id == '710', fs))
        enento20en_filing.json_download_path = 'test_json'
        enento20en_filing.package_download_path = 'test_package'
        enento20en_filing.xhtml_download_path = 'test_xhtml'
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        assert 'json_download_path' not in pd_data
        assert 'package_download_path' not in pd_data
        assert 'xhtml_download_path' not in pd_data
        assert '507' in pd_data['api_id']
        assert '1495' in pd_data['api_id']


class TestResourceCollection_entities_get_pandas_data:
    """Test method ResourceCollection.get_pandas_data for FilingSet.entities."""

    def test_e_defaults(self, get_oldest3_fi_entities_filingset):
        """Test default parameter values."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False
            )
        i = pd_data['api_id'].index('548')
        assert pd_data['identifier'][i] == '743700EPLUWXE25HGM03'
        assert pd_data['name'][i] == 'Enento Group Oyj'
        assert 'api_entity_filings_url' not in pd_data
        assert isinstance(pd_data['query_time'][i], datetime)
        assert 'request_url' not in pd_data
        assert 'filings' not in pd_data
        assert '383' in pd_data['api_id']
        assert '1120' in pd_data['api_id']

    def test_e_attr_names_2cols(self, get_oldest3_fi_entities_filingset):
        """Test attr_names defining 2 columns."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=['api_id', 'name'],
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False
            )
        i = pd_data['api_id'].index('548')
        assert len(pd_data) == 2
        assert pd_data['name'][i] == 'Enento Group Oyj'
        assert '383' in pd_data['api_id']
        assert '1120' in pd_data['api_id']

    @pytest.mark.datetime
    def test_e_strip_timezone_true(
            self, get_oldest3_fi_entities_filingset):
        """Test strip_timezone=True."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False
            )
        for i in range(len(fs)):
            assert isinstance(pd_data['query_time'][i], datetime)
            assert pd_data['query_time'][i].tzinfo is None

    @pytest.mark.datetime
    def test_e_strip_timezone_false(self, get_oldest3_fi_entities_filingset):
        """Test strip_timezone=False."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=False,
            date_as_datetime=True,
            include_urls=False
            )
        for i in range(len(fs)):
            assert isinstance(pd_data['query_time'][i], datetime)
            assert pd_data['query_time'][i].tzinfo is not None

    def test_e_include_urls_true(
            self, get_oldest3_fi_entities_filingset, monkeypatch):
        """Test include_urls=True."""
        monkeypatch.setattr(xf.options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=True
            )
        i = pd_data['api_id'].index('548')
        assert pd_data['api_entity_filings_url'][i] == 'https://filings.xbrl.org/api/entities/743700EPLUWXE25HGM03/filings'
        assert pd_data['request_url'][i].startswith('https://filings.xbrl.org/')
        assert '383' in pd_data['api_id']
        assert '1120' in pd_data['api_id']

    def test_e_include_urls_true(
            self, get_oldest3_fi_entities_filingset, monkeypatch):
        """Test include_urls=True."""
        monkeypatch.setattr(xf.options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=True
            )
        i = pd_data['api_id'].index('548')
        assert pd_data['api_entity_filings_url'][i] == 'https://filings.xbrl.org/api/entities/743700EPLUWXE25HGM03/filings'
        assert pd_data['request_url'][i].startswith('https://filings.xbrl.org/')
        assert '383' in pd_data['api_id']
        assert '1120' in pd_data['api_id']


class TestResourceCollection_validation_messages_get_pandas_data:
    """Test method ResourceCollection.get_pandas_data for FilingSet.validation_messages."""

    def test_vm_defaults(self, get_oldest3_fi_vmessages_filingset):
        """Test default parameter values."""
        e_api_ids = {
            '5464', '5465', '5466', '5467', '5468', '5469', '5470', '5471', '5472',
            '5473', '5474', '5475', '5476', '5477', '5478', '8662', '8663', '8664',
            '8665', '8666', '8667', '8668', '8669', '8670', '8671', '8672', '8673',
            '8674', '8675', '8676', '8677', '8678', '8679', '8680', '16748',
            '16749', '16750', '16751', '16752', '16753', '16754', '16755', '16756',
            '16757', '16758'
            }
        e_5464_text = (
            'Calculation inconsistent from ifrs-full:NoncurrentAssets in link '
            'role http://www.oriola.com/roles/Assets reported sum 537,300,000 '
            'computed sum 537,400,000 context c-3 unit u-1 '
            'unreportedContributingItems none'
            )
        fs: xf.FilingSet = get_oldest3_fi_vmessages_filingset()
        vmsg_5464: xf.ValidationMessage = next(filter(
            lambda vmsg: vmsg.api_id == '5464', fs.validation_messages))
        pd_data = fs.validation_messages.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False
            )
        i = pd_data['api_id'].index('5464')
        assert len(pd_data['api_id']) == len(e_api_ids)
        assert pd_data['severity'][i] == 'INCONSISTENCY'
        assert pd_data['text'][i] == e_5464_text
        assert pd_data['code'][i] == 'xbrl.5.2.5.2:calcInconsistency'
        assert pd_data['filing_api_id'][i] == '507'
        assert pd_data['calc_computed_sum'][i] == vmsg_5464.calc_computed_sum
        assert pd_data['calc_reported_sum'][i] == vmsg_5464.calc_reported_sum
        assert pd_data['calc_context_id'][i] == vmsg_5464.calc_context_id
        assert pd_data['calc_line_item'][i] == vmsg_5464.calc_line_item
        assert pd_data['calc_short_role'][i] == vmsg_5464.calc_short_role
        assert pd_data['calc_unreported_items'][i] == vmsg_5464.calc_unreported_items
        assert pd_data['duplicate_greater'][i] is None
        assert pd_data['duplicate_lesser'][i] is None
        assert isinstance(pd_data['query_time'][i], datetime)
        assert 'request_url' not in pd_data
        assert 'filing' not in pd_data
        for e_api_id in e_api_ids:
            assert e_api_id in pd_data['api_id']

    def test_vm_attr_names_2cols(self, get_oldest3_fi_vmessages_filingset):
        """Test attr_names defining 2 columns."""
        e_api_ids = {
            '5464', '5465', '5466', '5467', '5468', '5469', '5470', '5471', '5472',
            '5473', '5474', '5475', '5476', '5477', '5478', '8662', '8663', '8664',
            '8665', '8666', '8667', '8668', '8669', '8670', '8671', '8672', '8673',
            '8674', '8675', '8676', '8677', '8678', '8679', '8680', '16748',
            '16749', '16750', '16751', '16752', '16753', '16754', '16755', '16756',
            '16757', '16758'
            }
        fs: xf.FilingSet = get_oldest3_fi_vmessages_filingset()
        pd_data = fs.validation_messages.get_pandas_data(
            attr_names=['api_id', 'severity'],
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False
            )
        i = pd_data['api_id'].index('5464')
        assert len(pd_data['api_id']) == len(e_api_ids)
        assert len(pd_data) == 2
        assert pd_data['severity'][i] == 'INCONSISTENCY'
        for e_api_id in e_api_ids:
            assert e_api_id in pd_data['api_id']
