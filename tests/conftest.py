"""
Shared pytest fixtures.

conftest.py is automatically loaded by pytest — no imports needed in test files.
Think of it as @BeforeEach setup that's available project-wide.
"""

import pytest
from datetime import datetime, timedelta

from tests.factories import make_backup_file, make_backup_files_range


@pytest.fixture
def now():
    """Fixed reference point for all time-based tests."""
    return datetime.now().replace(
        hour=12,
        minute=0,
        second=0,
        microsecond=0,
    )


@pytest.fixture
def single_file(now):
    return [make_backup_file(now)]


@pytest.fixture
def empty_files():
    return []