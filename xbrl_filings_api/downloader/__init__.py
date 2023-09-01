"""
Standalone package for downloading files sequentially or in parallel.

Parallel downloading provides an asynchronous iterator.

"""


from .download_processor import (
    download, download_async, download_parallel, download_parallel_async,
    download_parallel_async_iter, validate_stem_pattern, stats
    )
from .download_specs import DownloadSpecs
