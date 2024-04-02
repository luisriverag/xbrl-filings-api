"""Define tests for `download_processor`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest
import requests
import responses

import xbrl_filings_api.downloader as downloader


def test_download_connection_error(tmp_path):
    """Test raising of `requests.ConnectionError`."""
    e_filename = 'test_download_connection_error.zip'
    url = f'https://filings.xbrl.org/download/{e_filename}'
    # `responses` used solely to block internet connection
    with responses.RequestsMock():
        with pytest.raises(requests.exceptions.ConnectionError):
            downloader.download(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
    empty_path = tmp_path / e_filename
    assert not empty_path.is_file()


def test_download_not_found_error(tmp_path):
    """Test raising of status 404 `requests.HTTPError`."""
    e_filename = 'test_download_not_found_error.zip'
    url = f'https://filings.xbrl.org/download/{e_filename}'
    with responses.RequestsMock() as rsps:
        rsps.add(
            method=responses.GET,
            url=url,
            status=404,
            )
        with pytest.raises(
                requests.exceptions.HTTPError,
                match=r'404 Client Error'):
            downloader.download(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=None,
                timeout=30.0
                )
    empty_path = tmp_path / e_filename
    assert not empty_path.is_file()


def test_download_original_filename(mock_url_response, tmp_path):
    """Test filename from URL will be used for saved file."""
    e_filename = 'test_download_original_filename.zip'
    path_str = None
    url = f'https://filings.xbrl.org/download/{e_filename}'
    with responses.RequestsMock() as rsps:
        mock_url_response(url, rsps)
        path_str = downloader.download(
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


def test_download_sha256_fail(
        mock_url_response, mock_response_sha256, tmp_path):
    """Test filename in attr `filename` will be used for saved file."""
    filename = 'test_download_sha256_fail.zip'
    e_filename = f'{filename}.corrupt'
    url = f'https://filings.xbrl.org/download/{filename}'
    e_file_sha256 = '0' * 64
    with responses.RequestsMock() as rsps:
        mock_url_response(url, rsps)
        # Raises CorruptDownloadError of downloader package
        with pytest.raises(downloader.CorruptDownloadError) as exc_info:
            downloader.download(
                url=url,
                to_dir=tmp_path,
                stem_pattern=None,
                filename=None,
                sha256=e_file_sha256,
                timeout=30.0
                )
        err = exc_info.value
        assert err.path == str(tmp_path / e_filename)
        assert err.url == url
        assert err.calculated_hash == mock_response_sha256
        assert err.expected_hash == e_file_sha256
        # downloader.CorruptDownloadError has no __str__
    corrupt_path = tmp_path / e_filename
    assert corrupt_path.is_file()
    assert corrupt_path.stat().st_size > 0
    success_path = tmp_path / filename
    assert not success_path.is_file()
