"""
Pytest configuration and fixtures for ScholarDoc tests.
"""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_config():
    """Return a sample ConversionConfig for testing."""
    from scholardoc import ConversionConfig

    return ConversionConfig()
