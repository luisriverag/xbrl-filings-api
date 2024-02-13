"""Examples of the library."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import logging
import tempfile
from pathlib import Path

import xbrl_filings_api as xf
from xbrl_filings_api import DownloadInfo, DownloadResult

# By default, log to temporary directory, such as environment variables
# "TMPDIR" or "TEMP"
LOGGING_DIR_PATH = Path(tempfile.gettempdir())
LOGGING_FILE_NAME = 'xbrl-filings-api_examples.log'

# Set up logging
logging.basicConfig(
    filename=str(LOGGING_DIR_PATH / LOGGING_FILE_NAME),
    encoding='utf-8',
    level=logging.DEBUG,
    format='{asctime} {levelname:3.3} {name}: {message}',
    style='{'
    )


async def print_progress_async():
    """
    Download all files of three latest additions to Finnish filings.

    Query three filings filed in Finland which were added latest to the
    index, download their XHTML, JSON and package files and print
    finished downloads in real time to prompt.
    """
    save_path = 'latest_finnish_fin_stmts'
    filings = xf.get_filings(
        filters={'country': 'FI'},
        sort='-added_time',
        max_size=3
        )

    dl_iter = filings.download_aiter(
        ['xhtml', 'json', 'package'], save_path, max_concurrent=4)
    result: DownloadResult
    async for result in dl_iter:
        print('\nDownloaded       ' + result.url)
        if result.path:
            res_info: DownloadInfo = result.info
            pretext = f'Saved {res_info.file} to'
            print(f'{pretext:<16} {result.path}')
        if result.err:
            print(result.err)

asyncio.run(print_progress_async())
