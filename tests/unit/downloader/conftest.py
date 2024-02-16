from typing import Union

import pytest
import responses

from xbrl_filings_api.downloader import DownloadSpecs


@pytest.fixture(scope='module')
def mock_response_data():
    """Arbitrary data to mock download."""
    return '0123456789' * 100


@pytest.fixture(scope='module')
def mock_response_data_charcount(mock_response_data):
    """Arbitrary data to mock download."""
    return len(mock_response_data)



@pytest.fixture(scope='module')
def mock_url_response(mock_response_data):
    """Function to add a `responses` mock URL with `mock_response_data` body."""
    def _mock_url_response(
            url: str, rsps: Union[responses.RequestsMock, None] = None):
        nonlocal mock_response_data
        if rsps is None:
            rsps = responses
        rsps.add(
            method=responses.GET,
            url=url,
            body=mock_response_data,
            headers={}
            )
    return _mock_url_response


@pytest.fixture
def plain_specs():
    """Function for a plain `DownloadSpecs` object."""
    def _plain_specs(url, path, *, info=None):
        return DownloadSpecs(
            url=url,
            to_dir=path,
            stem_pattern=None,
            filename=None,
            sha256=None,
            info=info
            )
    return _plain_specs


@pytest.fixture
def hashfail_specs():
    """Function for a failing `sha256` hash check `DownloadSpecs` object."""
    def _hashfail_specs(url, path, *, info=None):
        e_file_sha256 = '0' * 64
        return DownloadSpecs(
            url=url,
            to_dir=path,
            stem_pattern=None,
            filename=None,
            sha256=e_file_sha256,
            info=info
            )
    return _hashfail_specs


@pytest.fixture
def renamed_specs():
    """Function for a ``_renamed`` suffixed file stem `DownloadSpecs` object."""
    def _renamed_specs(url, path, *, info=None):
        return DownloadSpecs(
            url=url,
            to_dir=path,
            stem_pattern='/name/_renamed',
            filename=None,
            sha256=None,
            info=info
            )
    return _renamed_specs
