"""Define class `UrlMock` for test fixture `urlmock`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from types import ModuleType
from typing import Union

import responses

MOCK_URL_PATH = Path(__file__).parent / 'mock_responses'


class UrlMock:
    """Define operations for URL mock responses."""

    def path(self, urlmock_name: str):
        """
        Get absolute file path of the mock URL collection file.

        Parameters
        ----------
        urlmock_name : str
            Name of the URL mock as defined in ``mock_upgrade.py``.
        """
        file_path = MOCK_URL_PATH / f'{urlmock_name}.yaml'
        if not file_path.is_file():
            msg = (
                'URL mock is not downloaded. Run script "mock_upgrade.py -n" '
                'to download defined but not yet downloaded mocks.'
                )
            raise Exception(msg)
        return str(file_path)

    def apply(
            self, rsps: Union[responses.RequestsMock, ModuleType],
            urlmock_name: str):
        """
        Get absolute file path of the mock URL collection file.

        Parameters
        ----------
        rsps : responses.RequestsMock or module responses
            The RequestsMock context to apply the URL mock.
        urlmock_name : str
            Name of the URL mock as defined in ``mock_upgrade.py``.
        """
        rsps._add_from_file(self.path(urlmock_name))
