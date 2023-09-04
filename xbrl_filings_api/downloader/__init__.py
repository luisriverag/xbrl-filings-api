"""
Standalone package for downloading files sequentially or in parallel.

Parallel downloading provides an asynchronous iterator.

"""


from xbrl_filings_api.download_processor import (
    download,
    download_async,
    download_parallel,
    download_parallel_async,
    download_parallel_async_iter,
    stats,
    validate_stem_pattern,
)
from xbrl_filings_api.download_specs import DownloadSpecs
