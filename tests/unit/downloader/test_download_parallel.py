"""Define tests for function `download_parallel`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
import requests
import responses
from responses.registries import OrderedRegistry

import xbrl_filings_api.downloader as downloader
import xbrl_filings_api.exceptions as xf_exceptions
from xbrl_filings_api.downloader import DownloadResult


def test_parallel_connection_error(plain_specs, tmp_path):
    """Test returning of `requests.ConnectionError`."""
    e_filename = 'test_parallel_connection_error.zip'
    url = f'https://filings.xbrl.org/download_parallel/{e_filename}'
    items = [plain_specs(url, tmp_path)]
    res_list = None
    with responses.RequestsMock() as rsps:
        res_list = downloader.download_parallel(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
    assert len(res_list) == 1
    assert res_list[0].url == url
    assert res_list[0].path is None
    assert isinstance(res_list[0].err, requests.exceptions.ConnectionError)
    empty_path = tmp_path / e_filename
    assert not empty_path.is_file()


def test_parallel_not_found_error(plain_specs, tmp_path):
    """Test returning of status 404 `requests.HTTPError`."""
    e_filename = 'test_parallel_not_found_error.zip'
    url = f'https://filings.xbrl.org/download_parallel/{e_filename}'
    items = [plain_specs(url, tmp_path)]
    res_list = None
    with responses.RequestsMock() as rsps:
        rsps.add(
            method=responses.GET,
            url=url,
            status=404,
            )
        res_list = downloader.download_parallel(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
    assert len(res_list) == 1
    assert res_list[0].url == url
    assert res_list[0].path is None
    assert isinstance(res_list[0].err, requests.exceptions.HTTPError)
    empty_path = tmp_path / e_filename
    assert not empty_path.is_file()


def test_parallel_original_filename(plain_specs, mock_url_response, tmp_path):
    """Test filename from URL will be used for saved file."""
    e_filename = 'test_parallel_original_filename.zip'
    url = f'https://filings.xbrl.org/download_parallel/{e_filename}'
    items = [plain_specs(url, tmp_path)]
    res_list: list[DownloadResult] = []
    with responses.RequestsMock() as rsps:
        mock_url_response(url, rsps)
        res_list = downloader.download_parallel(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
    assert len(res_list) == 1
    assert res_list[0].url == url
    assert res_list[0].err is None
    save_path = Path(res_list[0].path)
    assert save_path.is_file()
    assert save_path.stat().st_size > 0
    assert save_path.name == e_filename


def test_parallel_sha256_fail(hashfail_specs, mock_url_response, tmp_path):
    """Test returning of `CorruptDownloadError` when `sha256` is incorrect."""
    filename = 'test_parallel_sha256_fail.zip'
    e_filename = f'{filename}.corrupt'
    url = f'https://filings.xbrl.org/download_parallel/{filename}'
    items = [hashfail_specs(url, tmp_path)]
    res_list: list[DownloadResult] = []
    with responses.RequestsMock() as rsps:
        mock_url_response(url, rsps)
        res_list = downloader.download_parallel(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
    assert len(res_list) == 1
    assert res_list[0].url == url
    assert isinstance(res_list[0].err, xf_exceptions.CorruptDownloadError)
    corrupt_path = tmp_path / e_filename
    assert corrupt_path.is_file()
    assert corrupt_path.stat().st_size > 0
    success_path = tmp_path / filename
    assert not success_path.is_file()


def test_sync_4_items_at_once(
        plain_specs, hashfail_specs, stem_renamed_specs,
        filename_renamed_specs, mock_url_response, tmp_path):
    """Test downloading 4 items with `max_concurrent` as None."""
    e_filestem = 'test_sync_4_items_at_once'
    url_prefix = 'https://filings.xbrl.org/download_parallel/'
    url_list = [f'{url_prefix}{e_filestem}_{n}.zip' for n in range(0, 5)]
    items = [
        plain_specs(url_list[1], tmp_path, info='test1'),
        hashfail_specs(url_list[2], tmp_path, info='test2'),
        stem_renamed_specs(url_list[3], tmp_path, info='test3'),
        filename_renamed_specs(url_list[4], tmp_path, info='test4'),
        ]
    res_list: list[DownloadResult] = []
    with responses.RequestsMock() as rsps:
        for url_n in range(1, 5):
            mock_url_response(url_list[url_n], rsps)
        res_list = downloader.download_parallel(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
    assert len(res_list) == 4
    for res in res_list:
        if res.info == 'test1':
            assert res.url == url_list[1]
            assert res.err is None
            save_path = Path(res.path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == f'{e_filestem}_1.zip'
        elif res.info == 'test2':
            assert res.url == url_list[2]
            assert isinstance(res.err, xf_exceptions.CorruptDownloadError)
            assert res.path is None
            corrupt_path = tmp_path / f'{e_filestem}_2.zip.corrupt'
            assert corrupt_path.is_file()
            assert corrupt_path.stat().st_size > 0
        elif res.info == 'test3':
            assert res.url == url_list[3]
            assert res.err is None
            save_path = Path(res.path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == f'{e_filestem}_3_renamed.zip'
        elif res.info == 'test4':
            assert res.url == url_list[4]
            assert res.err is None
            save_path = Path(res.path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == f'renamed.abc'
        else:
            assert pytest.fail('Info is other than one defined in test')


def test_sync_4_items_max_concurrent_2(
        plain_specs, hashfail_specs, stem_renamed_specs,
        filename_renamed_specs, mock_url_response, tmp_path):
    """Test downloading 4 items with `max_concurrent` as 2."""
    e_filestem = 'test_sync_4_items_max_concurrent_2'
    url_prefix = 'https://filings.xbrl.org/download_parallel/'
    url_list = [f'{url_prefix}{e_filestem}_{n}.zip' for n in range(0, 5)]
    items = [
        plain_specs(url_list[1], tmp_path, info='test1'),
        hashfail_specs(url_list[2], tmp_path, info='test2'),
        stem_renamed_specs(url_list[3], tmp_path, info='test3'),
        filename_renamed_specs(url_list[4], tmp_path, info='test4'),
        ]
    res_list: list[DownloadResult] = []
    with responses.RequestsMock() as rsps:
        for url_n in range(1, 5):
            mock_url_response(url_list[url_n], rsps)
        res_list = downloader.download_parallel(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
    assert len(res_list) == 4
    for res in res_list:
        if res.info == 'test1':
            assert res.url == url_list[1]
            assert res.err is None
            save_path = Path(res.path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == f'{e_filestem}_1.zip'
        elif res.info == 'test2':
            assert res.url == url_list[2]
            assert isinstance(res.err, xf_exceptions.CorruptDownloadError)
            assert res.path is None
            corrupt_path = tmp_path / f'{e_filestem}_2.zip.corrupt'
            assert corrupt_path.is_file()
            assert corrupt_path.stat().st_size > 0
        elif res.info == 'test3':
            assert res.url == url_list[3]
            assert res.err is None
            save_path = Path(res.path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == f'{e_filestem}_3_renamed.zip'
        elif res.info == 'test4':
            assert res.url == url_list[4]
            assert res.err is None
            save_path = Path(res.path)
            assert save_path.is_file()
            assert save_path.stat().st_size > 0
            assert save_path.name == f'renamed.abc'
        else:
            assert pytest.fail('Info is other than one defined in test')


def test_sync_items_request_start_order(
        plain_specs, mock_url_response, tmp_path):
    """Test that downloads are started according to order of `items`, n=50, max_concurrent=17."""
    e_filestem = 'test_sync_items_request_start_order'
    url_prefix = 'https://filings.xbrl.org/download_parallel/'
    item_count = 50
    max_concurrent = 17
    url_list = [
        f'{url_prefix}{e_filestem}_{n}.zip'
        for n in range(0, item_count+1)
        ]
    items = [
        plain_specs(url_list[test_n], tmp_path, info=f'test{test_n}')
        for test_n in range(1, item_count+1)
        ]
    with responses.RequestsMock(registry=OrderedRegistry) as rsps:
        for url_n in range(1, item_count+1):
            mock_url_response(url_list[url_n], rsps)
        downloader.download_parallel(
            items=items,
            max_concurrent=max_concurrent,
            timeout=30.0
            )
