"""Define tests for downloading files of `Filing` objects."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import hashlib
import urllib.parse
from pathlib import Path, PurePosixPath

import pytest
import responses

import xbrl_filings_api as xf
import xbrl_filings_api.exceptions as xf_exceptions


@pytest.fixture(scope='module')
def get_filing_or_filingset():
    """Function for single Filing or FilingSet."""
    def _get_filing_or_filingset(libclass):
        mock_dir_path = Path(__file__).parent.parent / 'mock_responses'
        if libclass is xf.Filing:
            fset = None
            with responses.RequestsMock() as rsps:
                rsps._add_from_file(str(mock_dir_path / 'asml22en.yaml'))
                fset = xf.get_filings(
                    filters={'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'},
                    sort=None,
                    max_size=1,
                    flags=xf.GET_ONLY_FILINGS,
                    add_api_params=None
                    )
            filing = next(iter(fset))
            return filing, [filing]
        if libclass is xf.FilingSet:
            fset = None
            with responses.RequestsMock() as rsps:
                rsps._add_from_file(str(mock_dir_path / 'oldest3_fi.yaml'))
                fset = xf.get_filings(
                    filters={'country': 'FI'},
                    sort='date_added',
                    max_size=3,
                    flags=xf.GET_ONLY_FILINGS,
                    add_api_params=None
                    )
            return fset, list(fset)
    return _get_filing_or_filingset


@pytest.fixture(scope='module')
def url_filename():
    """Function for getting the filename from URL."""
    def _url_filename(url):
        url_path = urllib.parse.urlparse(url).path
        return PurePosixPath(url_path).name
    return _url_filename


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json(
        libclass, get_filing_or_filingset, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download`."""
    target, filings = get_filing_or_filingset(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
        target.download(
            files='json',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        save_path = Path(filing.json_download_path)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == url_filename(filing.json_url)


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_json(
        libclass, get_filing_or_filingset, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download_aiter`."""
    target, filings = get_filing_or_filingset(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
        dliter = target.download_aiter(
            files='json',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
        res: xf.DownloadResult
        async for res in dliter:
            assert res.err is None
            res_info: xf.DownloadInfo = res.info
            assert res_info.file == 'json'
            filing: xf.Filing = res_info.obj
            assert res.url == filing.json_url
            assert res.path == filing.json_download_path
            save_path = Path(filing.json_download_path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == url_filename(filing.json_url)


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_package_no_check_corruption(
        libclass, get_filing_or_filingset, url_filename, mock_url_response, tmp_path):
    """Test downloading `package_url` by `download` without sha256 check."""
    target, filings = get_filing_or_filingset(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.package_url, rsps)
        target.download(
            files='package',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=False,
            max_concurrent=None
            )
    for filing in filings:
        save_path = Path(filing.package_download_path)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == url_filename(filing.package_url)


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_package_no_check_corruption(
        libclass, get_filing_or_filingset, url_filename, mock_url_response, tmp_path):
    """Test downloading `package_url` by `download_aiter` without sha256 check."""
    target, filings = get_filing_or_filingset(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.package_url, rsps)
        dliter = target.download_aiter(
            files='package',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=False,
            max_concurrent=None
            )
        res: xf.DownloadResult
        async for res in dliter:
            assert res.err is None
            res_info: xf.DownloadInfo = res.info
            assert res_info.file == 'package'
            filing: xf.Filing = res_info.obj
            assert res.url == filing.package_url
            assert res.path == filing.package_download_path
            save_path = Path(filing.package_download_path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == url_filename(filing.package_url)
