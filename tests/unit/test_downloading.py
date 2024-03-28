"""Define tests for downloading files of `Filing` objects."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import re
import urllib.parse
from pathlib import Path, PurePosixPath

import pytest
import responses

import xbrl_filings_api as xf


@pytest.fixture(scope='module')
def get_asml22en_or_oldest3_fi(urlmock):
    """Function for single Filing or FilingSet of either `asml22en` or `oldest3_fi`."""
    def _get_asml22en_or_oldest3_fi(libclass):
        if libclass is xf.Filing:
            fset = None
            with responses.RequestsMock() as rsps:
                urlmock.apply(rsps, 'asml22en')
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
                urlmock.apply(rsps, 'oldest3_fi')
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
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        tmp_path):
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
        mock_response_sha256, tmp_path):
    """Test downloading `package_url` by `download` with sha256 check failure."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    e_expected_hash = '0'*64
    e_paths = set()
    e_urls = set()
    for filing in filings:
        filename = f'{url_filename(filing.package_url)}.corrupt'
        e_paths.add(str(tmp_path / filename))
        e_urls.add(filing.package_url)
        # Filing objects are mutable
        filing.package_sha256 = e_expected_hash
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.package_url, rsps)
        # Raises CorruptDownloadError of root library
        with pytest.raises(xf.CorruptDownloadError) as exc_info:
            target.download(
                files='package',
                to_dir=tmp_path,
                stem_pattern=None,
                check_corruption=True,
                max_concurrent=None
                )
        err = exc_info.value
        assert err.path in e_paths
        assert err.url in e_urls
        assert err.calculated_hash == mock_response_sha256
        assert err.expected_hash == e_expected_hash
        parts = str(err).split(', ')
        assert len(parts) == 4
        attr_re = re.compile(r'(calculated_hash|expected_hash|path|url)=')
        for part in parts:
            assert attr_re.match(part)
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
        mock_response_sha256, tmp_path):
    """Test downloading `package_url` by `download_aiter` with sha256 check failure."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    e_expected_hash = '0'*64
    e_paths = set()
    e_urls = set()
    for filing in filings:
        filename = f'{url_filename(filing.package_url)}.corrupt'
        e_paths.add(str(tmp_path / filename))
        e_urls.add(filing.package_url)
        # Filing objects are mutable
        filing.package_sha256 = e_expected_hash
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
        attr_re = re.compile(r'(calculated_hash|expected_hash|path|url)=')
        async for res in dliter:
            # `err` has CorruptDownloadError of root library
            assert isinstance(res.err, xf.CorruptDownloadError)
            assert res.err.path in e_paths
            assert res.err.url in e_urls
            assert res.err.calculated_hash == mock_response_sha256
            assert res.err.expected_hash == e_expected_hash
            parts = str(res.err).split(', ')
            assert len(parts) == 4
            for part in parts:
                assert attr_re.match(part)

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


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json_to_dir_none(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        tmp_path, monkeypatch):
    """Test downloading `json_url` with to_dir=None (cwd) by `download`."""
    monkeypatch.chdir(tmp_path)
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
        target.download(
            files='json',
            to_dir=None,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        save_path = Path(filing.json_download_path)
        assert save_path.parent == tmp_path
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == url_filename(filing.json_url)


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_json_to_dir_none(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response,
        tmp_path, monkeypatch):
    """Test downloading `json_url` with to_dir=None (cwd) by `download_aiter`."""
    monkeypatch.chdir(tmp_path)
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
        dliter = target.download_aiter(
            files='json',
            to_dir=None,
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
            assert save_path.parent == tmp_path
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == url_filename(filing.json_url)


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_viewer_raise(
        libclass, get_asml22en_or_oldest3_fi, url_filename, tmp_path):
    """Test raising when downloading `viewer_url` by `download`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with pytest.raises(ValueError, match=r"File 'viewer' is not among"):
        target.download(
            files='viewer',
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        empty_path = tmp_path / url_filename(filing.viewer_url)
        assert not empty_path.is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_viewer_raise(
        libclass, get_asml22en_or_oldest3_fi, url_filename, tmp_path):
    """Test raising when downloading `viewer_url` by `download_aiter`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    dliter = target.download_aiter(
        files='viewer',
        to_dir=tmp_path,
        stem_pattern=None,
        check_corruption=True,
        max_concurrent=None
        )
    with pytest.raises(ValueError, match=r"File 'viewer' is not among"):
        async for _ in dliter:
            pass
    for filing in filings:
        empty_path = tmp_path / url_filename(filing.viewer_url)
        assert not empty_path.is_file()


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_files_as_int_raise(
        libclass, get_asml22en_or_oldest3_fi, url_filename, tmp_path):
    """Test raising when `files` is int by `download`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with pytest.raises(
            TypeError,
            match=r"Parameter 'files' is none of str, Iterable or Mapping" ):
        target.download(
            files=2,
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        empty_path = tmp_path / url_filename(filing.viewer_url)
        assert not empty_path.is_file()


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_files_as_int_raise(
        libclass, get_asml22en_or_oldest3_fi, url_filename, tmp_path):
    """Test raising when `files` is int by `download_aiter`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    dliter = target.download_aiter(
        files=2,
        to_dir=tmp_path,
        stem_pattern=None,
        check_corruption=True,
        max_concurrent=None
        )
    with pytest.raises(
            TypeError,
            match=r"Parameter 'files' is none of str, Iterable or Mapping" ):
        async for _ in dliter:
            pass
    for filing in filings:
        empty_path = tmp_path / url_filename(filing.viewer_url)
        assert not empty_path.is_file()


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json_missing_log(
        libclass, get_asml22en_or_oldest3_fi, tmp_path, caplog):
    """Test logging when JSON is missing by `download`."""
    caplog.set_level(logging.WARNING)
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        filing.json_url = None
    target.download(
        files='json',
        to_dir=tmp_path,
        stem_pattern=None,
        check_corruption=True,
        max_concurrent=None
        )
    for filing in filings:
        assert filing.json_download_path is None
    record: logging.LogRecord
    counter = 0
    for record in caplog.records:
        if (record.levelname == 'WARNING'
                and record.message.startswith('JSON not available for Filing(')):
            counter += 1
    assert counter == len(filings)


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_json_missing_log(
        libclass, get_asml22en_or_oldest3_fi, tmp_path, caplog):
    """Test logging when JSON is missing by `download_aiter`."""
    caplog.set_level(logging.WARNING)
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        filing.json_url = None
    dliter = target.download_aiter(
        files='json',
        to_dir=tmp_path,
        stem_pattern=None,
        check_corruption=True,
        max_concurrent=None
        )
    async for _ in dliter:
        pass
    for filing in filings:
        assert filing.json_download_path is None
    record: logging.LogRecord
    counter = 0
    for record in caplog.records:
        if (record.levelname == 'WARNING'
                and record.message.startswith('JSON not available for Filing(')):
            counter += 1
    assert counter == len(filings)


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_package_missing_log(
        libclass, get_asml22en_or_oldest3_fi, tmp_path, caplog):
    """Test logging when package is missing by `download`."""
    caplog.set_level(logging.WARNING)
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        filing.package_url = None
    target.download(
        files='package',
        to_dir=tmp_path,
        stem_pattern=None,
        check_corruption=True,
        max_concurrent=None
        )
    for filing in filings:
        assert filing.package_download_path is None
    record: logging.LogRecord
    counter = 0
    for record in caplog.records:
        if (record.levelname == 'WARNING'
                and record.message.startswith('Package not available for Filing(')):
            counter += 1
    assert counter == len(filings)


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_package_missing_files_mapping_log(
        libclass, get_asml22en_or_oldest3_fi, tmp_path, caplog):
    """Test logging when package is missing (files as mapping) by `download`."""
    caplog.set_level(logging.WARNING)
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    for filing in filings:
        filing.package_url = None
    files={
        'package': xf.DownloadItem(
            filename=None,
            to_dir=tmp_path,
            stem_pattern=None)
        }
    target.download(
        files=files,
        to_dir=None,
        stem_pattern=None,
        check_corruption=True,
        max_concurrent=None
        )
    for filing in filings:
        assert filing.package_download_path is None
    record: logging.LogRecord
    counter = 0
    for record in caplog.records:
        if (record.levelname == 'WARNING'
                and record.message.startswith('Package not available for Filing(')):
            counter += 1
    assert counter == len(filings)


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json_and_xhtml(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` and `xhtml_url` by `download`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
            mock_url_response(filing.xhtml_url, rsps)
        target.download(
            files=['json', 'xhtml'],
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        json_path = Path(filing.json_download_path)
        assert json_path.is_file()
        assert json_path.stat().st_size > 0
        assert json_path.name == url_filename(filing.json_url)
        xhtml_path = Path(filing.xhtml_download_path)
        assert xhtml_path.is_file()
        assert xhtml_path.stat().st_size > 0
        assert xhtml_path.name == url_filename(filing.xhtml_url)


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_json_and_xhtml(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` and `xhtml_url` by `download_aiter`."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
            mock_url_response(filing.xhtml_url, rsps)
        dliter = target.download_aiter(
            files=['json', 'xhtml'],
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
        res: xf.DownloadResult
        async for res in dliter:
            assert res.err is None
            res_info: xf.DownloadInfo = res.info
            save_path = None
            filing: xf.Filing = res_info.obj
            if res_info.file == 'json':
                assert res.url == filing.json_url
                assert res.path == filing.json_download_path
                save_path = Path(filing.json_download_path)
                assert save_path.name == url_filename(filing.json_url)
            elif res_info.file == 'xhtml':
                assert res.url == filing.xhtml_url
                assert res.path == filing.xhtml_download_path
                save_path = Path(filing.xhtml_download_path)
                assert save_path.name == url_filename(filing.xhtml_url)
            else:
                pytest.fail('DownloadResult.info.file not "json" or "xhtml"')
            assert save_path.is_file()
            assert save_path.stat().st_size > 0


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json_DownloadItem(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download` with `DownloadItem` setup."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
        target.download(
            files={
                'json': xf.DownloadItem(
                    filename=None,
                    to_dir=None,
                    stem_pattern=None
                    )
                },
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
async def test_download_aiter_json_DownloadItem(
        libclass, get_asml22en_or_oldest3_fi, url_filename, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download_aiter` with `DownloadItem` setup."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
        dliter = target.download_aiter(
            files={
                'json': xf.DownloadItem(
                    filename=None,
                    to_dir=None,
                    stem_pattern=None
                    )
                },
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


def test_download_json_Filing_DownloadItem_rename(
        get_asml22en_or_oldest3_fi, mock_url_response, tmp_path):
    """Test downloading `json_url` by `Filing.download` with `DownloadItem` renamed setup."""
    filing: xf.Filing
    filing, _ = get_asml22en_or_oldest3_fi(xf.Filing)
    with responses.RequestsMock() as rsps:
        mock_url_response(filing.json_url, rsps)
        filing.download(
            files={
                'json': xf.DownloadItem(
                    filename='renamed_file.abc',
                    to_dir=None,
                    stem_pattern=None
                    )
                },
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    save_path = Path(filing.json_download_path)
    assert save_path.is_file()
    assert save_path.stat().st_size > 0
    assert save_path.name == 'renamed_file.abc'


def test_download_json_FilingSet_DownloadItem_rename_raise(
        get_asml22en_or_oldest3_fi, tmp_path):
    """Test raising when downloading `json_url` by `FilingSet.download` with `DownloadItem` renamed setup."""
    filingset: xf.FilingSet
    filingset, filings = get_asml22en_or_oldest3_fi(xf.FilingSet)
    filing: xf.Filing
    with pytest.raises(
            ValueError,
            match=r'The attribute DownloadItem\.filename may not be other than None'):
        filingset.download(
            files={
                'json': xf.DownloadItem(
                    filename='renamed_file.abc',
                    to_dir=None,
                    stem_pattern=None
                    )
                },
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        assert filing.json_download_path is None
    save_path = tmp_path / 'renamed_file.abc'
    assert not save_path.is_file()


@pytest.mark.asyncio
async def test_download_aiter_json_Filing_DownloadItem_rename(
        get_asml22en_or_oldest3_fi, mock_url_response, tmp_path):
    """Test downloading `json_url` by `Filing.download_aiter` with `DownloadItem` renamed setup."""
    filing: xf.Filing
    filing, _ = get_asml22en_or_oldest3_fi(xf.Filing)
    with responses.RequestsMock() as rsps:
        mock_url_response(filing.json_url, rsps)
        dliter = filing.download_aiter(
            files={
                'json': xf.DownloadItem(
                    filename='renamed_file.abc',
                    to_dir=None,
                    stem_pattern=None
                    )
                },
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
            assert save_path.name == 'renamed_file.abc'


@pytest.mark.asyncio
async def test_download_aiter_json_FilingSet_DownloadItem_rename_raise(
        get_asml22en_or_oldest3_fi, tmp_path):
    """Test raising when downloading `json_url` by `FilingSet.download_aiter` with `DownloadItem` renamed setup."""
    filingset: xf.FilingSet
    filingset, filings = get_asml22en_or_oldest3_fi(xf.FilingSet)
    dliter = filingset.download_aiter(
        files={
            'json': xf.DownloadItem(
                filename='renamed_file.abc',
                to_dir=None,
                stem_pattern=None
                )
            },
        to_dir=tmp_path,
        stem_pattern=None,
        check_corruption=True,
        max_concurrent=None
        )
    with pytest.raises(
            ValueError,
            match=r'The attribute DownloadItem\.filename may not be other than None'):
        async for _ in dliter:
            pass
    for filing in filings:
        assert filing.json_download_path is None
    save_path = tmp_path / 'renamed_file.abc'
    assert not save_path.is_file()


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json_DownloadItem_2_to_dir(
        libclass, get_asml22en_or_oldest3_fi, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download` with `DownloadItem` 2 different to_dir."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    json_path = tmp_path / 'json'
    xhtml_path = tmp_path / 'xhtml'
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
            mock_url_response(filing.xhtml_url, rsps)
        target.download(
            files={
                'json': xf.DownloadItem(
                    filename=None,
                    to_dir=json_path,
                    stem_pattern=None
                    ),
                'xhtml': xf.DownloadItem(
                    filename=None,
                    to_dir=xhtml_path,
                    stem_pattern=None
                    ),
            },
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        json_dl_path = Path(filing.json_download_path)
        assert json_dl_path.parent == json_path
        assert json_dl_path.is_file()
        assert json_dl_path.stat().st_size > 0
        xhtml_dl_path = Path(filing.xhtml_download_path)
        assert xhtml_dl_path.parent == xhtml_path
        assert xhtml_dl_path.is_file()
        assert xhtml_dl_path.stat().st_size > 0


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_json_DownloadItem_2_to_dir(
        libclass, get_asml22en_or_oldest3_fi, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download_aiter` 2 different to_dir."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    json_path = tmp_path / 'json'
    xhtml_path = tmp_path / 'xhtml'
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
            mock_url_response(filing.xhtml_url, rsps)
        dliter = target.download_aiter(
            files={
                'json': xf.DownloadItem(
                    filename=None,
                    to_dir=json_path,
                    stem_pattern=None
                    ),
                'xhtml': xf.DownloadItem(
                    filename=None,
                    to_dir=xhtml_path,
                    stem_pattern=None
                    ),
            },
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
        res: xf.DownloadResult
        async for res in dliter:
            assert res.err is None
            res_info: xf.DownloadInfo = res.info
            res_path = Path(res.path)
            assert res_path.is_file()
            assert res_path.stat().st_size > 0
            if res_info.file == 'json':
                assert res_path.parent == json_path
            elif res_info.file == 'xhtml':
                assert res_path.parent == xhtml_path
            else:
                pytest.fail(f'Additional files: {res_info.file!r}')


@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
def test_download_json_DownloadItem_2_stem_pattern(
        libclass, get_asml22en_or_oldest3_fi, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download` with `DownloadItem` 2 different stem_pattern."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
            mock_url_response(filing.xhtml_url, rsps)
        target.download(
            files={
                'json': xf.DownloadItem(
                    filename=None,
                    to_dir=None,
                    stem_pattern='json_/name/'
                    ),
                'xhtml': xf.DownloadItem(
                    filename=None,
                    to_dir=None,
                    stem_pattern='xhtml_/name/'
                    ),
            },
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
    for filing in filings:
        json_dl_path = Path(filing.json_download_path)
        assert json_dl_path.name.startswith('json_')
        xhtml_dl_path = Path(filing.xhtml_download_path)
        assert xhtml_dl_path.name.startswith('xhtml_')


@pytest.mark.asyncio
@pytest.mark.parametrize('libclass', [xf.Filing, xf.FilingSet])
async def test_download_aiter_json_DownloadItem_2_stem_pattern(
        libclass, get_asml22en_or_oldest3_fi, mock_url_response, tmp_path):
    """Test downloading `json_url` by `download_aiter` 2 different stem_pattern."""
    target, filings = get_asml22en_or_oldest3_fi(libclass)
    filing: xf.Filing
    with responses.RequestsMock() as rsps:
        for filing in filings:
            mock_url_response(filing.json_url, rsps)
            mock_url_response(filing.xhtml_url, rsps)
        dliter = target.download_aiter(
            files={
                'json': xf.DownloadItem(
                    filename=None,
                    to_dir=None,
                    stem_pattern='json_/name/'
                    ),
                'xhtml': xf.DownloadItem(
                    filename=None,
                    to_dir=None,
                    stem_pattern='xhtml_/name/'
                    ),
            },
            to_dir=tmp_path,
            stem_pattern=None,
            check_corruption=True,
            max_concurrent=None
            )
        res: xf.DownloadResult
        async for res in dliter:
            assert res.err is None
            res_info: xf.DownloadInfo = res.info
            res_path = Path(res.path)
            if res_info.file == 'json':
                assert res_path.name.startswith('json_')
            elif res_info.file == 'xhtml':
                assert res_path.name.startswith('xhtml_')
            else:
                pytest.fail(f'Additional files: {res_info.file!r}')
