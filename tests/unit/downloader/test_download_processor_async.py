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
            self, mock_url_response, tmp_path):
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
                timeout=30
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_with_filename(
            self, mock_url_response, tmp_path):
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
                timeout=30
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_stem_pattern_filename(
            self, mock_url_response, tmp_path):
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
                timeout=30
                )
        save_path = Path(path_str)
        assert save_path.is_file()
        assert save_path.stat().st_size > 0
        assert save_path.name == e_filename

    async def test_sha256_success(
            self, mock_url_response, mock_response_data,
            tmp_path):
        url = 'https://filings.xbrl.org/download_async/test_sha256_success.zip'
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
                timeout=30
                )

    async def test_sha256_fail(
            self, mock_url_response, tmp_path):
        e_filename = 'test_sha256_fail.zip'
        url = f'https://filings.xbrl.org/download_async/{e_filename}'
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
                    timeout=30
                    )
        corrupt_path = tmp_path / f'{e_filename}.corrupt'
        assert corrupt_path.is_file()
        assert corrupt_path.stat().st_size > 0
        success_path = tmp_path / e_filename
        assert not success_path.is_file()

    async def test_autocreate_dir(
            self, mock_url_response, tmp_path):
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
                timeout=30
                )
        save_path = Path(path_str)
        e_path = deep_path / e_filename
        assert save_path == e_path
        assert save_path.is_file()
        assert save_path.stat().st_size > 0

    async def test_overwrite_file(
            self, mock_url_response, tmp_path):
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
                timeout=30
                )
        save_path = Path(path_str)
        assert save_path == existing_path
        assert save_path.is_file()
        assert save_path.stat().st_size != existing_size

    async def test_filename_not_available(
            self, mock_url_response, tmp_path):
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
                timeout=30
                )
            path_b = await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30
                )
        save_path_a = Path(path_a)
        assert save_path_a.is_file()
        assert save_path_a.stat().st_size > 0
        assert save_path_a.name == 'file0001'
        save_path_b = Path(path_b)
        assert save_path_b.is_file()
        assert save_path_b.stat().st_size > 0
        assert save_path_b.name == 'file0002'


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
