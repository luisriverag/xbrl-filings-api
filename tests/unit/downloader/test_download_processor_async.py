"""Define tests for `download_processor`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import hashlib
import urllib.parse
from pathlib import Path, PurePosixPath

import pytest
import pytest_asyncio
import responses

import xbrl_filings_api as xf
import xbrl_filings_api.downloader as downloader
import xbrl_filings_api.exceptions as xf_exceptions
from xbrl_filings_api.downloader import DownloadSpecs

pytestmark = pytest.mark.asyncio


class Test_download_async:
    """Test method `xbrl_filings_api.downloader.download_async`."""

    async def test_original_filename(
            self, mock_file_url, mock_url_response, tmp_path):
        url = mock_file_url(1)
        e_filename = PurePosixPath(urllib.parse.urlparse(url).path).name
        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(1, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_with_filename(
            self, mock_file_url, mock_url_response, tmp_path):
        url = mock_file_url(1)
        e_filename = 'filename.abc'
        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(1, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=e_filename,
                sha256=None,
                timeout=30
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_stem_pattern_filename(
            self, mock_file_url, mock_url_response, tmp_path):
        url = mock_file_url(1)
        ppath = PurePosixPath(urllib.parse.urlparse(url).path)
        e_filename = ppath.stem + '_test' + ppath.suffix
        path_str = None
        with responses.RequestsMock() as rsps:
            mock_url_response(1, rsps)
            path_str = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern='/name/_test',
                filename=None,
                sha256=None,
                timeout=30
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_sha256_success(
            self, mock_file_url, mock_url_response, mock_response_data,
            tmp_path):
        url = mock_file_url(1)
        fhash = hashlib.sha256(
            string=mock_response_data.encode(encoding='utf-8'),
            usedforsecurity=False
            )
        # No CorruptDownloadError raised
        with responses.RequestsMock() as rsps:
            mock_url_response(1, rsps)
            await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=fhash.hexdigest(),
                timeout=30
                )

    async def test_sha256_fail(
            self, mock_file_url, mock_url_response, tmp_path):
        url = mock_file_url(1)
        e_file_sha256 = '0' * 64
        with responses.RequestsMock() as rsps:
            mock_url_response(1, rsps)
            with pytest.raises(xf_exceptions.CorruptDownloadError):
                await downloader.download_async(
                    url=url,
                    to_dir=tmp_path,
                    stem_pattern=None,
                    filename=None,
                    sha256=e_file_sha256,
                    timeout=30
                    )


# @pytest.mark.asyncio(scope='module')
# class Test_download_parallel_async:
#     async def test_download_parallel_async(self):
#         save_path = await downloader.download_parallel_async(
#             items=[DownloadSpecs(
#                 url='str',
#                 to_dir='str | PurePath',
#                 stem_pattern='str | None = None',
#                 filename='str | None = None',
#                 sha256='str | None = None',
#                 info='Any = None'
#                 )],
#             max_concurrent=1,
#             timeout=30
#             )

# @pytest.mark.asyncio(scope='module')
# class Test_download_parallel_aiter:
#     async def test_download_parallel_aiter(self):
#         dl_aiter = await downloader.download_parallel_aiter(
#             items=[DownloadSpecs(
#                 url='str',
#                 to_dir='str | PurePath',
#                 stem_pattern='str | None = None',
#                 filename='str | None = None',
#                 sha256='str | None = None',
#                 info='Any = None'
#                 )],
#             max_concurrent=1,
#             timeout=30
#             )
#         for res in dl_aiter:
#             res
