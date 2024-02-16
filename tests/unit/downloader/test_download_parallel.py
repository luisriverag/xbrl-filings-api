"""Define tests for function `download_parallel`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
import requests
import responses

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
