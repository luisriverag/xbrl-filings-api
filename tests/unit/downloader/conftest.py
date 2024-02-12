import pytest
import pytest_asyncio
import responses


@pytest.fixture(scope='module')
def mock_file_url():
    def _mock_file_url(num: int):
        return f'https://filings.xbrl.org/files/dl_{num:02}.zip'
    return _mock_file_url


@pytest.fixture(scope='module')
def mock_response_data(mock_file_url):
    return '0123456789' * 100



@pytest.fixture(scope='module')
def mock_url_response(mock_file_url, mock_response_data):
    def _mock_url_response(
            num: int, rsps: responses.RequestsMock | None = None):
        nonlocal mock_file_url, mock_response_data
        if rsps is None:
            rsps = responses
        rsps.add(
            method=responses.GET,
            url=mock_file_url(num),
            body=mock_response_data,
            headers={}
            )
    return _mock_url_response
