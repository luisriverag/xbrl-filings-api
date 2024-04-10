"""
Example functions and coroutines for the library.

This module may be run as a script. The script asks which example or
examples to run.
"""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import inspect
import logging
import re
import tempfile
from pathlib import Path
from types import FunctionType

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
        limit=3
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
    print()


def open_ixbrl_viewer_in_browser():
    """Open Inline XBRL viewer in web browser of ASML 2022 English."""
    filings = xf.get_filings(
        filters={'filing_index': '724500Y6DUVHQD6OXN27-2022-12-31-ESEF-NL-0'}
        )
    filing = next(iter(filings))
    filing.open()


# Runner script
if __name__ == '__main__':
    print(
        'Select an example function to run. Write the number of the example\n'
        'or a comma-separated list of numbers.\n'
        )
    globaldict = locals()
    ex_names = {
        i+1: funcname
        for i, funcname in enumerate(
            aname for aname, val in globaldict.items() if (
                isinstance(val, FunctionType)
                and aname != 'namedtuple'
                )
            )
        }
    for num, funcname in ex_names.items():
        print(f'{num}: {funcname}')
        func = globaldict[funcname]
        print('\n'.join([
            ' '*4 + dline.lstrip()
            for dline in func.__doc__.strip().split('\n')
            ]) + '\n')
    while input_str := input('Example number(s): '):
        nums = [int(num) for num in input_str.split(',')]
        for num in nums:
            funcname = ex_names[num]
            func = globaldict[funcname]
            print(re.sub(
                r' +""".+"""\n', '', inspect.getsource(func),
                count=1, flags=re.DOTALL))
            if inspect.iscoroutinefunction(func):
                asyncio.run(func())
            else:
                func()
