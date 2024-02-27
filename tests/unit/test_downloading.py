"""Define tests for downloading files of `Filing` objects."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import urllib.parse
from pathlib import Path, PurePosixPath

import pytest
import responses

import xbrl_filings_api as xf
import xbrl_filings_api.exceptions as xf_exceptions


@pytest.fixture(scope='module')
def get_asml22en_or_oldest3_fi():
    """Function for single Filing or FilingSet."""
    def _get_asml22en_or_oldest3_fi(libclass):
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
    return _get_asml22en_or_oldest3_fi


@pytest.fixture(scope='module')
def url_filename():
    """Function for getting the filename from URL."""
    def _url_filename(url):
        url_path = urllib.parse.urlparse(url).path
        return PurePosixPath(url_path).name
    return _url_filename


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
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
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download_aiter`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
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
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `package_url` by `download` without sha256 check."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
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
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `package_url` by `download_aiter` without sha256 check."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
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


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_package_check_corruption_success(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        mock_response_sha256, tmp_path):
    """Test downloading `package_url` by `download` with sha256 check success."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        # Filing objects are mutable
        filing.package_sha256 = mock_response_sha256
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.package_url, rsps)
        # Must not raise CorruptDownloadError
        target.download(
            files='package',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        save_path = Path(filing.package_download_path)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == url_filename(filing.package_url)


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_package_check_corruption_success(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        mock_response_sha256, tmp_path):
    """Test downloading `package_url` by `download_aiter` with sha256 check success."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        # Filing objects are mutable
        filing.package_sha256 = mock_response_sha256
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.package_url, rsps)
        # Must not raise CorruptDownloadError
        dliter = target.download_aiter(
            files='package',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
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


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_package_check_corruption_fail(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        tmp_path):
    """Test downloading `package_url` by `download` with sha256 check failure."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        # Filing objects are mutable
        filing.package_sha256 = '0'*64
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.package_url, rsps)
        with pytest.raises(xf_exceptions.CorruptDownloadError):
            target.download(
                files='package',
                to_dir=tmp_path,
                stem_pattern=None,
                check_corruption=True,
                max_concurrent=None
                )
    for filing in filings:
        filename = url_filename(filing.package_url)
        corrupt_path = tmp_path / f'{filename}.corrupt'
        assert corrupt_path.is_file()
        assert corrupt_path.stat().st_size > 0
        success_path = tmp_path / filename
        assert not success_path.is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_package_check_corruption_fail(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        tmp_path):
    """Test downloading `package_url` by `download_aiter` with sha256 check failure."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        # Filing objects are mutable
        filing.package_sha256 = '0'*64
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.package_url, rsps)
        dliter = target.download_aiter(
            files='package',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
        res: xf.DownloadResult
        async for res in dliter:
            assert isinstance(res.err, xf_exceptions.CorruptDownloadError)
            res_info: xf.DownloadInfo = res.info
            assert res_info.file == 'package'
            filing: xf.Filing = res_info.obj
            assert res.url == filing.package_url
            assert res.path is None
            assert filing.package_download_path is None


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_xhtml(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        tmp_path):
    """Test downloading `xhtml_url` by `download`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.xhtml_url, rsps)
        target.download(
            files='xhtml',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        save_path = Path(filing.xhtml_download_path)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == url_filename(filing.xhtml_url)


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_xhtml(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        tmp_path):
    """Test downloading `xhtml_url` by `download_aiter`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.xhtml_url, rsps)
        dliter = target.download_aiter(
            files='xhtml',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
        res: xf.DownloadResult
        async for res in dliter:
            assert res.err is None
            res_info: xf.DownloadInfo = res.info
            assert res_info.file == 'xhtml'
            filing: xf.Filing = res_info.obj
            assert res.url == filing.xhtml_url
            assert res.path == filing.xhtml_download_path
            save_path = Path(filing.xhtml_download_path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == url_filename(filing.xhtml_url)
