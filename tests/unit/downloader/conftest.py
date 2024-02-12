import pytest
import pytest_asyncio
import responses


@pytest.fixture(scope='module')
def mock_response_data():
    return '0123456789' * 100



@pytest.fixture(scope='module')
def mock_url_response(mock_response_data):
    def _mock_url_response(
            url: str, rsps: responses.RequestsMock | None = None):
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
