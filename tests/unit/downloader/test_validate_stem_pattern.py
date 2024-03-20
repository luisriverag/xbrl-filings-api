"""Define tests for function `validate_stem_pattern`."""

# SPDX-FileCopyrightText: 2023 Lauri Salmela <lauri.m.salmela@gmail.com>
#
# SPDX-License-Identifier: MIT

import pytest

import xbrl_filings_api.downloader as downloader


def test_none():
    """Test no raised ValueError when None."""
    downloader.validate_stem_pattern(None)


def test_placeholder_middle():
    """Test no raised ValueError when placeholder in middle."""
    downloader.validate_stem_pattern('prefix/name/suffix')


def test_placeholder_beginning():
    """Test no raised ValueError when placeholder in beginning."""
    downloader.validate_stem_pattern('/name/suffix')


def test_placeholder_end():
    """Test no raised ValueError when placeholder in end."""
    downloader.validate_stem_pattern('prefix/name/')


def test_placeholder_partial():
    """Test raised ValueError when placeholder is partial."""
    with pytest.raises(ValueError, match=r'Placeholder .+ missing in'):
        downloader.validate_stem_pattern('prefix/namesuffix')


def test_placeholder_not_given():
    """Test raised ValueError when placeholder is missing."""
    with pytest.raises(ValueError, match=r'Placeholder .+ missing in'):
        downloader.validate_stem_pattern('prefixsuffix')
