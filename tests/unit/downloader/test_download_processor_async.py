"""Define tests for `download_processor`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import hashlib
from pathlib import Path

import pytest
import requests
import responses

import xbrl_filings_api.downloader as downloader
import xbrl_filings_api.exceptions as xf_exceptions
from xbrl_filings_api.downloader import DownloadResult, DownloadSpecs

pytestmark = pytest.mark.asyncio


class Test_download_async:
    """Test function `download_async`."""

    async def test_connection_error(self, mock_url_response, tmp_path):
        e_filename = 'test_connection_error.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
        with responses.RequestsMock() as rsps:
            with pytest.raises(requests.ConnectionError):
                path_str = await downloader.download_async(
                    url=url,
                    to_dir=tmp_path,
                    stem_pattern=None,
                    filename=None,
                    sha256=None,
                    timeout=30.0
                    )

    async def test_original_filename(self, mock_url_response, tmp_path):
        e_filename = 'test_original_filename.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_with_filename(self, mock_url_response, tmp_path):
        url = 'https://filings.xbrl.org/download_async/test_with_filename.zip'
        e_filename = 'filename.abc'
        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=e_filename,
                sha256=None,
                timeout=30.0
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_stem_pattern_filename(self, mock_url_response, tmp_path):
        url = 'https://filings.xbrl.org/download_async/test_stem_pattern_filename.zip'
        e_filename = 'test_stem_pattern_filename' + '_test' + '.zip'
        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern='/name/_test',
                filename=None,
                sha256=None,
                timeout=30.0
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_stem_pattern_no_placeholder(self, tmp_path):
        e_filename = 'test_stem_pattern_no_placeholder.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
        e_filename = 'test_stem_pattern_filename' + '_test' + '.zip'
        with pytest.raises(ValueError, match="Placeholder '/name/' missing"):
            await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern='test',
                filename=None,
                sha256=None,
                timeout=30.0
                )
        save_path = tmp_path / e_filename
        assert not save_path.is_file()

    async def test_to_dir_as_string(self, mock_url_response, tmp_path):
        e_filename = 'test_to_dir_as_string.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=str(tmp_path),
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_sha256_success(
            self, mock_url_response, mock_response_data, tmp_path):
        e_filename = 'test_sha256_success.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
        fhash = hashlib.sha256(
            string=mock_response_data.encode(encoding='utf-8'),
            usedforsecurity=False
            )
        # No CorruptDownloadError raised
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=fhash.hexdigest(),
                timeout=30.0
                )
        save_path = tmp_path / e_filename
        assert save_path.is_file()
        assert save_path.stat().st_size > 0

    async def test_sha256_fail(self, mock_url_response, tmp_path):
        filename = 'test_sha256_fail.zip'
        e_filename = f'{filename}.corrupt'
        url = f'https://filings.xbrl.org/download_async/{filename}'
        e_file_sha256 = '0' * 64
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            with pytest.raises(xf_exceptions.CorruptDownloadError):
                await downloader.download_async(
                    url=url,
                    to_dir=tmp_path,
                    stem_pattern=None,
                    filename=None,
                    sha256=e_file_sha256,
                    timeout=30.0
                    )
        corrupt_path = tmp_path / e_filename
        assert corrupt_path.is_file()
        assert corrupt_path.stat().st_size > 0
        success_path = tmp_path / filename
        assert not success_path.is_file()

    async def test_autocreate_dir(self, mock_url_response, tmp_path):
        e_filename = 'test_autocreate_dir.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
        path_str = None
        deep_path = tmp_path / 'newdir' / 'anotherdir'
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=deep_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
        save_path = Path(path_str)
        e_path = deep_path / e_filename
        assert save_path == e_path
        assert save_path.is_file()
        assert save_path.stat().st_size > 0

    async def test_overwrite_file(self, mock_url_response, tmp_path):
        e_filename = 'test_overwrite_file.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'

        existing_path = tmp_path / e_filename
        existing_size = None
        with open(existing_path, 'wb') as f:
            existing_size = f.write(b'\x20')

        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
        save_path = Path(path_str)
        assert save_path == existing_path
        assert save_path.is_file()
        assert save_path.stat().st_size != existing_size

    async def test_filename_not_available(self, mock_url_response, tmp_path):
        url = 'https://filings.xbrl.org/'
        path_a = path_b = None
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            path_a = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
            path_b = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
        save_path_a = Path(path_a)
        assert save_path_a.is_file()
        assert save_path_a.stat().st_size > 0
        assert save_path_a.name == 'file0001'
        save_path_b = Path(path_b)
        assert save_path_b.is_file()
        assert save_path_b.stat().st_size > 0
        assert save_path_b.name == 'file0002'


class Test_download_parallel_aiter:
    """Test function `download_parallel_aiter`."""

    async def test_aiter_connection_error(self, mock_url_response, tmp_path):
        e_filename = 'test_aiter_connection_error.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
        items = [
            DownloadSpecs(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                info=None)
            ]
        dl_res = None
        with responses.RequestsMock() as rsps:
            dl_aiter = downloader.download_parallel_aiter(
                items=items,
                max_concurrent=None,
                timeout=30.0
                )
            dl_res: DownloadResult = await anext(dl_aiter)
        assert dl_res.url == url
        assert dl_res.path is None
        assert isinstance(dl_res.err, requests.ConnectionError)

    async def test_aiter_original_filename(self, mock_url_response, tmp_path):
        e_filename = 'test_aiter_original_filename.zip'
        url = f'https://filings.xbrl.org/download_parallel_aiter/{e_filename}'
        items = [
            DownloadSpecs(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                info=None)
            ]
        dl_res = None
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            dl_aiter = downloader.download_parallel_aiter(
                items=items,
                max_concurrent=None,
                timeout=30.0
                )
            dl_res: DownloadResult = await anext(dl_aiter)
            with pytest.raises(StopAsyncIteration):
                await anext(dl_aiter)
        assert dl_res.url == url
        assert dl_res.err is None
        save_path = Path(dl_res.path)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_aiter_sha256_fail(self, mock_url_response, tmp_path):
        filename = 'test_aiter_sha256_fail.zip'
        e_filename = f'{filename}.corrupt'
        e_file_sha256 = '0' * 64
        url = f'https://filings.xbrl.org/download_async/{filename}'
        items = [
            DownloadSpecs(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=e_file_sha256,
                info=None)
            ]
        with responses.RequestsMock() as rsps:
            mock_url_response(url, rsps)
            dl_aiter = downloader.download_parallel_aiter(
                items=items,
                max_concurrent=None,
                timeout=30.0
                )
            dl_res: DownloadResult = await anext(dl_aiter)
        assert dl_res.url == url
        assert isinstance(dl_res.err, xf_exceptions.CorruptDownloadError)
        corrupt_path = tmp_path / e_filename
        assert corrupt_path.is_file()
        assert corrupt_path.stat().st_size > 0
        success_path = tmp_path / filename
        assert not success_path.is_file()

    # async def test_3_items_at_once(self, mock_url_response, tmp_path):
    # async def test_3_items_sequentially(self, mock_url_response, tmp_path):
    # async def test_3_items_max_concurrent_2(self, mock_url_response, tmp_path):
