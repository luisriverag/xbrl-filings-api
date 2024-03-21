"""
Define unit tests for method `get_pandas_data` of `FilingSet` and
`ResourceCollection`.

Tests with integration test focus are found from module
`integration.test_pandas_data`.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from datetime import date

import pandas as pd
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
        df = pd.DataFrame(data=pd_data)
        enento20en = df[df['api_id'] == '710']
        i = enento20en.index.array[0]
        assert enento20en.at[i, 'country'] == 'FI'
        assert enento20en.at[i, 'filing_index'] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert enento20en.at[i, 'language'] == 'en'
        assert enento20en.at[i, 'error_count'] == 0
        assert enento20en.at[i, 'inconsistency_count'] == 19
        assert enento20en.at[i, 'warning_count'] == 0
        assert 'added_time_str' not in enento20en.columns.array
        assert 'processed_time_str' not in enento20en.columns.array
        assert 'entity_api_id' not in enento20en.columns.array
        assert 'json_url' not in enento20en.columns.array
        assert 'package_url' not in enento20en.columns.array
        assert 'viewer_url' not in enento20en.columns.array
        assert 'xhtml_url' not in enento20en.columns.array
        assert 'request_url' not in enento20en.columns.array
        assert 'json_download_path' not in enento20en.columns.array
        assert 'package_download_path' not in enento20en.columns.array
        assert 'xhtml_download_path' not in enento20en.columns.array
        assert enento20en.at[i, 'package_sha256'] == 'ab0c60224c225ba3921188514ecd6c37af6a947f68a5c3a0c6eb34abfaae822b'
        assert 'entity' not in enento20en.columns.array
        assert 'validation_messages' not in enento20en.columns.array
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array

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
        df = pd.DataFrame(data=pd_data)
        assert len(df.columns.array) == 3
        enento20en = df[df['api_id'] == '710']
        i = enento20en.index.array[0]
        assert enento20en.at[i, 'filing_index'] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert enento20en.at[i, 'last_end_date'] == pd.Timestamp('2020-12-31')
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array

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
        df = pd.DataFrame(data=pd_data)
        assert len(df.columns.array) == 4
        enento20en = df[df['api_id'] == '710']
        i = enento20en.index.array[0]
        assert enento20en.at[i, 'filing_index'] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert enento20en.at[i, 'last_end_date'] == pd.Timestamp('2020-12-31')
        assert enento20en.at[i, 'entity.name'] == 'Enento Group Oyj'
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array

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
        df = pd.DataFrame(data=pd_data)
        enento20en = df[df['api_id'] == '710']
        i = enento20en.index.array[0]
        assert enento20en.at[i, 'filing_index'] == '743700EPLUWXE25HGM03-2020-12-31-ESEF-FI-0'
        assert 'entity_api_id' not in enento20en.columns.array
        assert enento20en.at[i, 'entity.api_id'] == '548'
        assert enento20en.at[i, 'entity.identifier'] == '743700EPLUWXE25HGM03'
        assert enento20en.at[i, 'entity.name'] == 'Enento Group Oyj'
        assert 'entity.api_entity_filings_url' not in enento20en.columns.array
        assert isinstance(enento20en.at[i, 'entity.query_time'], pd.Timestamp)
        assert 'entity.request_url' not in enento20en.columns.array
        assert 'entity.filings' not in enento20en.columns.array
        assert 'entity' not in enento20en.columns.array
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array

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
        df = pd.DataFrame(data=pd_data)
        enento20en = df[df['api_id'] == '710']
        i = enento20en.index.array[0]
        assert enento20en.at[i, 'json_url'] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31 EN.json'
        assert enento20en.at[i, 'package_url'] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31_EN.zip'
        assert enento20en.at[i, 'viewer_url'] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31_EN/reports/ixbrlviewer.html'
        assert enento20en.at[i, 'xhtml_url'] == 'https://filings.xbrl.org/743700EPLUWXE25HGM03/2020-12-31/ESEF/FI/0/ENENTO-2020-12-31_EN/reports/ENENTO-2020-12-31 EN.html'
        assert enento20en.at[i, 'request_url'].startswith('https://filings.xbrl.org/api/filings?')
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array

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
        df = pd.DataFrame(data=pd_data)
        enento20en = df[df['api_id'] == '710']
        i = enento20en.index.array[0]
        assert 'entity_api_id' not in enento20en.columns.array
        assert enento20en.at[i, 'entity.api_id'] == '548'
        assert enento20en.at[i, 'entity.identifier'] == '743700EPLUWXE25HGM03'
        assert enento20en.at[i, 'entity.name'] == 'Enento Group Oyj'
        assert enento20en.at[i, 'entity.api_entity_filings_url'] == 'https://filings.xbrl.org/api/entities/743700EPLUWXE25HGM03/filings'
        assert isinstance(enento20en.at[i, 'entity.query_time'], pd.Timestamp)
        assert enento20en.at[i, 'entity.request_url'].startswith('https://filings.xbrl.org/api/filings?')
        assert 'entity.filings' not in enento20en.columns.array
        assert 'entity' not in enento20en.columns.array
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array

    def test_include_paths_true(self, get_oldest3_fi_filingset):
        """Test include_paths=True."""
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
        df = pd.DataFrame(data=pd_data)
        enento20en = df[df['api_id'] == '710']
        i = enento20en.index.array[0]
        assert enento20en.at[i, 'json_download_path'] == 'test_json'
        assert enento20en.at[i, 'package_download_path'] == 'test_package'
        assert enento20en.at[i, 'xhtml_download_path'] == 'test_xhtml'
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array

    def test_include_paths_true_no_data(self, get_oldest3_fi_filingset):
        """Test include_paths=True but all paths values are None."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
        pd_data = fs.get_pandas_data(
            attr_names=None,
            with_entity=False,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=True
            )
        df = pd.DataFrame(data=pd_data)
        enento20en = df[df['api_id'] == '710']
        assert 'json_download_path' not in enento20en.columns.array
        assert 'package_download_path' not in enento20en.columns.array
        assert 'xhtml_download_path' not in enento20en.columns.array
        assert '507' in df['api_id'].array
        assert '1495' in df['api_id'].array


class TestResourceCollection_entities_get_pandas_data:
    """Test method ResourceCollection.get_pandas_data for FilingSet.entities."""

    def test_defaults(self, get_oldest3_fi_entities_filingset):
        """Test default parameter values."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        df = pd.DataFrame(data=pd_data)
        enento = df[df['api_id'] == '548']
        i = enento.index.array[0]
        assert enento.at[i, 'identifier'] == '743700EPLUWXE25HGM03'
        assert enento.at[i, 'name'] == 'Enento Group Oyj'
        assert 'api_entity_filings_url' not in enento.columns.array
        assert isinstance(enento.at[i, 'query_time'], pd.Timestamp)
        assert 'request_url' not in enento.columns.array
        assert 'filings' not in enento.columns.array
        assert '383' in df['api_id'].array
        assert '1120' in df['api_id'].array

    def test_attr_names_2cols(self, get_oldest3_fi_entities_filingset):
        """Test attr_names defining 2 columns."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=['api_id', 'name'],
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        df = pd.DataFrame(data=pd_data)
        enento = df[df['api_id'] == '548']
        i = enento.index.array[0]
        assert len(enento.columns.array) == 2
        assert enento.at[i, 'name'] == 'Enento Group Oyj'
        assert '383' in df['api_id'].array
        assert '1120' in df['api_id'].array

    @pytest.mark.datetime
    def test_strip_timezone_true(
            self, get_oldest3_fi_entities_filingset):
        """Test strip_timezone=True."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        assert pd_data['query_time'][0].tzinfo is None

    @pytest.mark.datetime
    def test_strip_timezone_false(self, get_oldest3_fi_entities_filingset):
        """Test strip_timezone=False."""
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=False,
            date_as_datetime=True,
            include_urls=False,
            include_paths=False
            )
        assert pd_data['query_time'][0].tzinfo is not None

    def test_include_urls_true(
            self, get_oldest3_fi_entities_filingset, monkeypatch):
        """Test include_urls=True."""
        monkeypatch.setattr(xf.options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=True,
            include_paths=False
            )
        df = pd.DataFrame(data=pd_data)
        enento = df[df['api_id'] == '548']
        i = enento.index.array[0]
        assert enento.at[i, 'api_entity_filings_url'] == 'https://filings.xbrl.org/api/entities/743700EPLUWXE25HGM03/filings'
        assert enento.at[i, 'request_url'].startswith('https://filings.xbrl.org/')
        assert '383' in df['api_id'].array
        assert '1120' in df['api_id'].array

    def test_include_urls_true(
            self, get_oldest3_fi_entities_filingset, monkeypatch):
        """Test include_urls=True."""
        monkeypatch.setattr(xf.options, 'entry_point_url', 'https://filings.xbrl.org/api/filings')
        fs: xf.FilingSet = get_oldest3_fi_entities_filingset()
        pd_data = fs.entities.get_pandas_data(
            attr_names=None,
            strip_timezone=True,
            date_as_datetime=True,
            include_urls=True,
            include_paths=False
            )
        df = pd.DataFrame(data=pd_data)
        enento = df[df['api_id'] == '548']
        i = enento.index.array[0]
        assert enento.at[i, 'api_entity_filings_url'] == 'https://filings.xbrl.org/api/entities/743700EPLUWXE25HGM03/filings'
        assert enento.at[i, 'request_url'].startswith('https://filings.xbrl.org/')
        assert '383' in df['api_id'].array
        assert '1120' in df['api_id'].array


class TestResourceCollection_validation_messages_get_pandas_data:
    """Test method ResourceCollection.get_pandas_data for FilingSet.validation_messages."""

    def test_defaults(self, get_oldest3_fi_vmessages_filingset):
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
            include_urls=False,
            include_paths=False
            )
        df = pd.DataFrame(data=pd_data)
        assert len(df.index.array) == len(e_api_ids)
        enento = df[df['api_id'] == '5464']
        i = enento.index.array[0]
        assert enento.at[i, 'severity'] == 'INCONSISTENCY'
        assert enento.at[i, 'text'] == e_5464_text
        assert enento.at[i, 'code'] == 'xbrl.5.2.5.2:calcInconsistency'
        assert enento.at[i, 'filing_api_id'] == '507'
        assert enento.at[i, 'calc_computed_sum'] == vmsg_5464.calc_computed_sum
        assert enento.at[i, 'calc_reported_sum'] == vmsg_5464.calc_reported_sum
        assert enento.at[i, 'calc_context_id'] == vmsg_5464.calc_context_id
        assert enento.at[i, 'calc_line_item'] == vmsg_5464.calc_line_item
        assert enento.at[i, 'calc_short_role'] == vmsg_5464.calc_short_role
        assert enento.at[i, 'calc_unreported_items'] == vmsg_5464.calc_unreported_items
        assert enento.at[i, 'duplicate_greater'] == vmsg_5464.duplicate_greater
        assert enento.at[i, 'duplicate_lesser'] == vmsg_5464.duplicate_lesser
        assert isinstance(enento.at[i, 'query_time'], pd.Timestamp)
        assert 'request_url' not in enento.columns.array
        assert 'filing' not in enento.columns.array
        for e_api_id in e_api_ids:
            assert e_api_id in df['api_id'].array

    def test_attr_names_2cols(self, get_oldest3_fi_vmessages_filingset):
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
            include_urls=False,
            include_paths=False
            )
        df = pd.DataFrame(data=pd_data)
        assert len(df.index.array) == len(e_api_ids)
        assert len(df.columns.array) == 2
        enento = df[df['api_id'] == '5464']
        i = enento.index.array[0]
        assert enento.at[i, 'severity'] == 'INCONSISTENCY'
        for e_api_id in e_api_ids:
            assert e_api_id in df['api_id'].array
