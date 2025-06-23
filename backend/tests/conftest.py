"""
Pytestの共通設定
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Provides a session-scoped asyncio event loop for use in tests.
    
    Yields:
        An asyncio event loop that persists for the duration of the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_valid_sql():
    """
    Return a sample valid SQL query string for selecting employees older than 25.
    """
    return "SELECT * FROM employees WHERE age > 25"


@pytest.fixture
def sample_invalid_sql():
    """
    Provides a sample SQL string containing invalid or destructive statements for testing purposes.
    
    Returns:
        str: An SQL string with DROP and DELETE statements.
    """
    return "DROP TABLE employees; DELETE FROM users;"