"""
Define download functions.

"""

# SPDX-FileCopyrightText: 2023-present Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import hashlib
import urllib.parse
from collections.abc import AsyncIterator
from pathlib import Path, PurePath
from typing import Any, Never, Optional

import requests

from xbrl_filings_api.download_specs import DownloadSpecs
from xbrl_filings_api.exceptions import CorruptDownloadError
from xbrl_filings_api.stat_counters import StatCounters

stats = StatCounters()


def download(
        url: str,
        to_dir: str | PurePath,
        stem_pattern: Optional[str] = None,
        filename: Optional[str] = None,
        sha256: Optional[str] = None
        ) -> str:
    """
    Download a file and optionally check if it is corrupt.

    See documentation of `download_async`.
    """
    return asyncio.run(download_async(
        url, to_dir, stem_pattern, filename, sha256))


async def download_async(
        url: str,
        to_dir: str | PurePath,
        stem_pattern: Optional[str] = None,
        filename: Optional[str] = None,
        sha256: Optional[str] = None
        ) -> str:
    """
    Download a file and optionally check if it is corrupt.

    The directories in `to_dir` will be created if they do not exist. If
    no `filename` is given, name is derived from `url`. If file already
    exists, it will be overwritten.

    If the `sha256` does not match with the hash of the downloaded file,
    `CorruptDownloadError` will be raised and the name of the downloaded
    file will be appended with ``.corrupt``.

    If download is interrupted, the file will be left with a suffix
    ``.unfinished``.

    If no name could be derived from `url`, the file will be named
    ``file0001``, ``file0002``, etc. In this case a new file is always
    created.

    Parameters
    ----------
    url : str
        URL to download.
    to_dir : str or pathlike
        Directory to save the file.
    stem_pattern : str, optional
        Pattern to add to the filename stems. Placeholder ``/name/``
        is always required.
    filename : str, optional
        Name to be used for the saved file.
    sha256 : str, optional
        Expected SHA-256 hash as a hex string. Case-insensitive. No
        hash is calculated if this parameter is not given.

    Returns
    -------
    coroutine of str
        Local path where the downloaded file was saved.

    Raises
    ------
    CorruptDownloadError
        Parameter `sha256` does not match the calculated hash.
    requests.HTTPError
        HTTP status error occurs.
    requests.ConnectionError
        Connection fails.
    """
    global stats

    validate_stem_pattern(stem_pattern)
    if not isinstance(to_dir, Path):
        to_dir = Path(to_dir)
    to_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        uqurl = urllib.parse.unquote(url)
        filename = urllib.parse.urlparse(uqurl).path.split('/')[-1]
        if filename.strip() == '':
            num = 1
            while (to_dir / f'file{num:04}').is_file():
                num += 1
            filename = f'file{num:04}'

    res = requests.get(url, stream=True)
    stats.item_counter += 1
    res.raise_for_status()

    hash = None
    if sha256:
        hash = hashlib.sha256()

    if stem_pattern:
        fnpath = Path(filename)
        filename = stem_pattern.replace('/name/', fnpath.stem) + fnpath.suffix

    save_path = Path.cwd() / to_dir / filename
    temp_path = save_path.with_suffix(f'{save_path.suffix}.unfinished')
    with open(temp_path, 'wb') as fd:
        for chunk in res.iter_content(chunk_size=None):
            fd.write(chunk)
            if sha256 and hash:
                hash.update(chunk)
            stats.byte_counter += len(chunk)
            await asyncio.sleep(0.0)

    if sha256 and hash:
        if hash.digest() != bytes.fromhex(sha256):
            corrupt_path = save_path.with_suffix(f'{save_path.suffix}.corrupt')
            corrupt_path.unlink(missing_ok=True)
            path = str(temp_path.rename(corrupt_path))

            calculated = hash.hexdigest().lower()
            expected = sha256.lower()
            raise CorruptDownloadError(path, url, calculated, expected)

    save_path.unlink(missing_ok=True)
    temp_path.rename(save_path)
    return str(save_path)


def download_parallel(
        items: list[DownloadSpecs], max_concurrent: int
        ) -> list[tuple[Any, str, str | Exception]]:
    """
    Download multiple files in parallel.

    See documentation of `download_parallel_async_iter`.

    Parameters
    ----------
    items : list of DownloadSpecs
    max_concurrent : int

    Returns
    -------
    list of tuple of (any, {str, Exception})
        List of `download_parallel_async_iter` yield values.
    """
    return asyncio.run(download_parallel_async(items, max_concurrent))


async def download_parallel_async(
        items: list[DownloadSpecs], max_concurrent: int
        ) -> list[tuple[Any, str, str | Exception]]:
    """
    Download multiple files in parallel.

    See documentation of `download_parallel_async_iter`.

    Parameters
    ----------
    items : list of DownloadSpecs
    max_concurrent : int

    Returns
    -------
    coroutine of list of tuple of (any, str, {str, Exception})
        List of `download_parallel_async_iter` yield values.
    """
    results = []
    async for item in download_parallel_async_iter(
            items, max_concurrent):
        results.append(item)
    return results


async def download_parallel_async_iter(
        items: list[DownloadSpecs], max_concurrent: int
        ) -> AsyncIterator[tuple[Any, str, str | Exception]]:
    """
    Download multiple files in parallel and return an asynchronous
    iterator.

    Calls method `download_async` via parameter `items`, see
    documentation.

    Parameters
    ----------
    items : list of DownloadSpecs
        Instances of `DownloadSpecs` accept the same parameters as
        method `download_async` with additional parameters `obj` and
        `attr_base`.
    max_concurrent : int
        Maximum number of simultaneous downloads allowed.

    Yields
    ------
    any
        Attribute `obj` from `items` item.
    str
        File format.
    {str, exception}
        Path where the file was saved or an exception.
    """
    dlque: asyncio.Queue[DownloadSpecs] = asyncio.Queue()
    for item in items:
        dlque.put_nowait(item)

    resultque: asyncio.Queue[tuple[Any, str, Exception | str]] = (
        asyncio.Queue())
    tasks: list[asyncio.Task] = []
    for worker_num in range(1, min(max_concurrent, len(items)) + 1):
        task = asyncio.create_task(
            _download_parallel_worker(dlque, resultque),
            name=f'worker-{worker_num}'
            )
        tasks.append(task)

    for _ in range(len(items)):
        result = await resultque.get()
        yield result

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


async def _download_parallel_worker(
        dlque: asyncio.Queue, resultque: asyncio.Queue) -> Never:
    """Coroutine worker for `download_parallel_async_iter`."""
    while True:
        item: DownloadSpecs = await dlque.get()
        try:
            path = await download_async(
                item.url, item.to_dir, item.stem_pattern, item.filename,
                item.sha256
                )
        except Exception as err:
            resultque.put_nowait((item.obj, item.attr_base, err))
        else:
            resultque.put_nowait((item.obj, item.attr_base, path))
        dlque.task_done()


def validate_stem_pattern(stem_pattern: str | None):
    """
    Validates `stem_pattern` parameter of module functions.

    Parameters
    ----------
    stem_pattern : str or None
        Stem pattern parameter.

    Raises
    ------
    ValueError
        When stem pattern is invalid.
    """
    if stem_pattern and '/name/' not in stem_pattern:
        msg = (
            "Placeholder '/name/' missing in 'stem_pattern' value "
            + repr(stem_pattern)
            )
        raise ValueError(msg)
