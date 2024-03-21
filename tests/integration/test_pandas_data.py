"""
Define integration tests for method `get_pandas_data` of `FilingSet` and
`ResourceCollection`.

Tests with unit test focus are found from module
`unit.test_pandas_data_unit`.

"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

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

    @pytest.mark.date
    def test_dates(self, get_oldest3_fi_filingset):
        """Test date columns."""
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
        assert enento20en.at[i, 'last_end_date'] == pd.Timestamp('2020-12-31')
        assert enento20en.at[i, 'reporting_date'] == pd.Timestamp('2020-12-31')
        assert isinstance(enento20en.at[i, 'query_time'], pd.Timestamp)

    @pytest.mark.datetime
    def test_datetimes(self, get_oldest3_fi_filingset):
        """Test datetime columns."""
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
        assert enento20en.at[i, 'added_time'] == pd.Timestamp('2021-05-18 00:00:00')
        assert enento20en.at[i, 'processed_time'] == pd.Timestamp('2023-01-18 11:02:18.936351')
        assert isinstance(enento20en.at[i, 'query_time'], pd.Timestamp)

    def test_with_entity_true_no_entity(self, get_oldest3_fi_filingset):
        """Test with_entity=True but no entities in FilingSet."""
        fs: xf.FilingSet = get_oldest3_fi_filingset()
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
        assert 'entity_api_id' not in enento20en.columns.array
        assert enento20en.at[i, 'entity.api_id'] is None
        assert enento20en.at[i, 'entity.identifier'] is None
        assert enento20en.at[i, 'entity.name'] is None
        assert 'entity.api_entity_filings_url' not in enento20en.columns.array
        assert enento20en.at[i, 'entity.query_time'] is None
        assert 'entity.request_url' not in enento20en.columns.array
        assert 'entity.filings' not in enento20en.columns.array
        assert 'entity' not in enento20en.columns.array
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
        assert enento.at[i, 'duplicate_greater'] is None
        assert enento.at[i, 'duplicate_lesser'] is None
        assert isinstance(enento.at[i, 'query_time'], pd.Timestamp)
        assert 'request_url' not in enento.columns.array
        assert 'filing' not in enento.columns.array
        for e_api_id in e_api_ids:
            assert e_api_id in df['api_id'].array
