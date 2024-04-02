"""Define tests for `_JSONTree`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import re

from xbrl_filings_api.__about__ import __version__


def test_main_print(capfd):
    """Test __main__ script."""
    # Import prints to stdout
    import xbrl_filings_api.__main__  # noqa: F401
    out, err = capfd.readouterr()
    assert re.fullmatch(f'\\n[a-z_]+ version {__version__}\n', out)
    assert err == ''
