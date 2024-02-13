"""Define tests for `download_processor`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import urllib.parse
from pathlib import Path, PurePosixPath

import responses

import xbrl_filings_api as xf
import xbrl_filings_api.downloader as downloader


@responses.activate
def test_download_original_filename(mock_url_response, tmp_path):
    e_filename = 'test_download_original_filename.zip'
    url = f'https://filings.xbrl.org/files/{e_filename}'
    mock_url_response(url)
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


@responses.activate
def test_download_with_filename(mock_url_response, tmp_path):
    url = 'https://filings.xbrl.org/files/test_download_with_filename.zip'
    mock_url_response(url)
    e_filename = 'filename.abc'
    path_str = downloader.download(
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


# def test_download_parallel():
#     save_path = downloader.download_parallel(
#         url='str',
#         to_dir='str | PurePath',
#         stem_pattern='str | None = None',
#         filename='str | None = None',
#         sha256='str | None = None',
#         timeout=30.0
#     )


# def test_validate_stem_pattern():
#     with pytest.raises(ValueError):
#         downloader.validate_stem_pattern('str | None')
