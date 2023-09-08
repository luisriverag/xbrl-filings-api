"""Examples of the library."""

import asyncio
import logging
import os.path
import tempfile

import xbrl_filings_api as xf

# Set up logging
logging.basicConfig(
    filename=os.path.join(
        tempfile.gettempdir(),
        'xbrl-filings-api_example.log'
        ),
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

    dl_iter = filings.download_async_iter(
        ['xhtml', 'json', 'package'], save_path, max_concurrent=4)
    async for result in dl_iter:
        print('\nDownloaded       ' + result.url)
        if result.path:
            pretext = f'Saved {result.file} to'
            print(f'{pretext:<16} {result.path}')
        if result.err:
            print(result.err)

asyncio.run(print_progress_async())
