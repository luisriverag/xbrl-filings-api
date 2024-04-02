"""
Define tests for `stats` of the downloader subpackage.

Not to be confused with the `stats` of the root module.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest
import responses

import xbrl_filings_api.downloader as downloader

pytestmark = pytest.mark.asyncio


async def test_item_counter_one_successful(
        mock_url_response, tmp_path, monkeypatch):
    """Test `item_counter` is 1 after one download_async call."""
    monkeypatch.setattr(downloader.stats, 'item_counter', 0, raising=True)
    e_filename = 'test_item_counter_one_successful.zip'
    url = f'https://filings.xbrl.org/stats/{e_filename}'
    with responses.RequestsMock() as rsps:
        mock_url_response(url, rsps)
        await downloader.download_async(
            url=url,
            to_dir=tmp_path,
            stem_pattern=None,
            filename=None,
            sha256=None,
            timeout=30.0
            )
    assert downloader.stats.item_counter == 1


async def test_item_counter_combined_2_successful_1_fail(
        plain_specs, mock_url_response, tmp_path, monkeypatch):
    """
    Test `item_counter` when downloading 2 items successfully and 1
    fail.
    """
    monkeypatch.setattr(downloader.stats, 'item_counter', 0, raising=True)
    e_filestem = 'test_item_counter_2_successful_1_fail'
    url_prefix = 'https://filings.xbrl.org/stats/'
    url_list = [f'{url_prefix}{e_filestem}_{n}.zip' for n in range(0, 4)]
    items = [
        plain_specs(url_list[1], tmp_path, info='test1'),
        plain_specs(url_list[2], tmp_path, info='test2'),
        plain_specs(url_list[3], tmp_path, info='test3'),
        ]
    with responses.RequestsMock() as rsps:
        mock_url_response(url_list[1], rsps)
        responses.add(
                method=responses.GET,
                url=url_list[2],
                status=404
                )
        mock_url_response(url_list[3], rsps)

        dl_aiter = downloader.download_parallel_aiter(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
        _ = [res async for res in dl_aiter]
    assert downloader.stats.item_counter == 2


async def test_item_counter_separate_1_plus_2_successful(
        plain_specs, mock_url_response, tmp_path, monkeypatch):
    """Test `item_counter` when downloading 1+2 items successfully."""
    monkeypatch.setattr(downloader.stats, 'item_counter', 0, raising=True)
    e_filestem = 'test_item_counter_separate_1_plus_2_successful'
    url_prefix = 'https://filings.xbrl.org/stats/'
    url_list = [f'{url_prefix}{e_filestem}_{n}.zip' for n in range(0, 4)]
    items = [
        plain_specs(url_list[2], tmp_path, info='test2'),
        plain_specs(url_list[3], tmp_path, info='test3'),
        ]
    with responses.RequestsMock() as rsps:
        for url_n in range(1, 4):
            mock_url_response(url_list[url_n], rsps)

        await downloader.download_async(
            url=url_list[1],
            to_dir=tmp_path,
            stem_pattern=None,
            filename=None,
            sha256=None,
            timeout=30.0
            )
        dl_aiter = downloader.download_parallel_aiter(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
        _ = [res async for res in dl_aiter]
    assert downloader.stats.item_counter == 3


async def test_byte_counter_one_successful(
        mock_response_data_charcount, mock_url_response, tmp_path,
        monkeypatch):
    """Test `byte_counter` is size after one download_async call."""
    monkeypatch.setattr(downloader.stats, 'byte_counter', 0, raising=True)
    e_filename = 'test_byte_counter_one_successful.zip'
    url = f'https://filings.xbrl.org/stats/{e_filename}'
    with responses.RequestsMock() as rsps:
        mock_url_response(url, rsps)
        await downloader.download_async(
            url=url,
            to_dir=tmp_path,
            stem_pattern=None,
            filename=None,
            sha256=None,
            timeout=30.0
            )
    assert downloader.stats.byte_counter == mock_response_data_charcount


async def test_byte_counter_combined_2_successful_1_fail(
        mock_response_data_charcount, plain_specs, mock_url_response, tmp_path,
        monkeypatch):
    """
    Test `byte_counter` when downloading 2 items successfully and 1
    fail.
    """
    monkeypatch.setattr(downloader.stats, 'byte_counter', 0, raising=True)
    e_filestem = 'test_byte_counter_2_successful_1_fail'
    url_prefix = 'https://filings.xbrl.org/stats/'
    url_list = [f'{url_prefix}{e_filestem}_{n}.zip' for n in range(0, 4)]
    items = [
        plain_specs(url_list[1], tmp_path, info='test1'),
        plain_specs(url_list[2], tmp_path, info='test2'),
        plain_specs(url_list[3], tmp_path, info='test3'),
        ]
    with responses.RequestsMock() as rsps:
        mock_url_response(url_list[1], rsps)
        responses.add(
                method=responses.GET,
                url=url_list[2],
                status=404
                )
        mock_url_response(url_list[3], rsps)

        dl_aiter = downloader.download_parallel_aiter(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
        _ = [res async for res in dl_aiter]
    assert downloader.stats.byte_counter == 2 * mock_response_data_charcount


async def test_byte_counter_separate_1_plus_2_successful(
        mock_response_data_charcount, plain_specs, mock_url_response, tmp_path,
        monkeypatch):
    """Test `byte_counter` when downloading 1+2 items successfully."""
    monkeypatch.setattr(downloader.stats, 'byte_counter', 0, raising=True)
    e_filestem = 'test_byte_counter_separate_1_plus_2_successful'
    url_prefix = 'https://filings.xbrl.org/stats/'
    url_list = [f'{url_prefix}{e_filestem}_{n}.zip' for n in range(0, 4)]
    items = [
        plain_specs(url_list[2], tmp_path, info='test2'),
        plain_specs(url_list[3], tmp_path, info='test3'),
        ]
    with responses.RequestsMock() as rsps:
        for url_n in range(1, 4):
            mock_url_response(url_list[url_n], rsps)

        await downloader.download_async(
            url=url_list[1],
            to_dir=tmp_path,
            stem_pattern=None,
            filename=None,
            sha256=None,
            timeout=30.0
            )
        dl_aiter = downloader.download_parallel_aiter(
            items=items,
            max_concurrent=None,
            timeout=30.0
            )
        _ = [res async for res in dl_aiter]
    assert downloader.stats.byte_counter == 3 * mock_response_data_charcount
