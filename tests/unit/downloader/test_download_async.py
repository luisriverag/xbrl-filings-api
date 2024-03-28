"""Define tests for coroutine `download_async`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import hashlib
import re
from pathlib import Path

import pytest
import requests
import responses

import xbrl_filings_api.downloader as downloader

pytestmark = pytest.mark.asyncio


async def test_connection_error(tmp_path):
    """Test raising of `requests.ConnectionError`."""
    e_filename = 'test_connection_error.zip'
    url = f'https://filings.xbrl.org/download_async/{e_filename}'
    with responses.RequestsMock() as rsps:
        with pytest.raises(requests.exceptions.ConnectionError):
            await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
    empty_path = tmp_path / e_filename
    assert not empty_path.is_file()


async def test_not_found_error(tmp_path):
    """Test raising of status 404 `requests.HTTPError`."""
    e_filename = 'test_not_found_error.zip'
    url = f'https://filings.xbrl.org/download_async/{e_filename}'
    with responses.RequestsMock() as rsps:
        rsps.add(
            method=responses.GET,
            url=url,
            status=404,
            )
        with pytest.raises(
                requests.exceptions.HTTPError,
                match=r'404 Client Error'):
            await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
    empty_path = tmp_path / e_filename
    assert not empty_path.is_file()


async def test_original_filename(mock_url_response, tmp_path):
    """Test filename from URL will be used for saved file."""
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


async def test_with_filename(mock_url_response, tmp_path):
    """Test filename in attr `filename` will be used for saved file."""
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


async def test_stem_pattern_filename(mock_url_response, tmp_path):
    """Test filename stem in attr `stem_pattern` will be used for saved file."""
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


async def test_stem_pattern_no_placeholder(tmp_path):
    """Test raising error when attr `stem_pattern` misses placeholder ``/name/``."""
    e_filename = 'test_stem_pattern_no_placeholder.zip'
    url = f'https://filings.xbrl.org/download_async/{e_filename}'
    e_filename = 'test_stem_pattern_filename' + '_test' + '.zip'
    with pytest.raises(ValueError, match=r"Placeholder '/name/' missing"):
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


async def test_to_dir_as_string(mock_url_response, tmp_path):
    """Test giving parameter `to_dir` as string."""
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


async def test_sha256_success(mock_url_response, mock_response_data, tmp_path):
    """Test correct `sha256` hash download succeeds."""
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


async def test_sha256_fail(mock_url_response, mock_response_sha256, tmp_path):
    """Test raising of `CorruptDownloadError` when `sha256` is incorrect."""
    filename = 'test_sha256_fail.zip'
    e_filename = f'{filename}.corrupt'
    url = f'https://filings.xbrl.org/download_async/{filename}'
    e_expected_hash = '0' * 64
    with responses.RequestsMock() as rsps:
        mock_url_response(url, rsps)
        # Raises CorruptDownloadError of downloader package
        with pytest.raises(downloader.CorruptDownloadError) as exc_info:
            await downloader.download_async(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=e_expected_hash,
                timeout=30.0
                )
        err = exc_info.value
        assert err.path == str(tmp_path / e_filename)
        assert err.url == url
        assert err.calculated_hash == mock_response_sha256
        assert err.expected_hash == e_expected_hash
        # downloader.CorruptDownloadError has no __str__
    corrupt_path = tmp_path / e_filename
    assert corrupt_path.is_file()
    assert corrupt_path.stat().st_size > 0
    success_path = tmp_path / filename
    assert not success_path.is_file()


async def test_autocreate_dir(mock_url_response, tmp_path):
    """Test the non-existent intermediary directories in `to_dir` are created."""
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


async def test_overwrite_file(mock_url_response, tmp_path):
    """Test an already existing file in the directory gets overwritten."""
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


async def test_filename_not_available(mock_url_response, tmp_path):
    """Test downloads with no derivable filename get filenames."""
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
