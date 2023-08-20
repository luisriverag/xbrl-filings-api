import asyncio

import xbrlfilingsapi as xf

# Query 3 filings filed in Finland which were added latest to the index,
# download their XHTML, JSON and package files and print finished
# downloads in real time to prompt.

save_path = 'latest_finnish_fin_stmts'
filings = xf.get_filings(filters={'country': 'FI'}, sort='-added_time', max_size=3)

async def print_progress_async(filings: xf.FilingSet):
    dl_iter = filings.download_async_iter(
        ['xhtml', 'json', 'package'], save_path, max_concurrent=4)
    async for filing, format, exc in dl_iter:
        print(f'\nDownloaded       ' + getattr(filing, f'{format}_url'))
        dl_path = getattr(filing, f'{format}_download_path')
        if dl_path:
            pretext = f'Saved {format} to'
            print(f'{pretext:<16} {dl_path}')
        if exc:
            print(exc)

asyncio.run(print_progress_async(filings))
