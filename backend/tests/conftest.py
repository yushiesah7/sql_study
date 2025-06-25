"""
Pytestの共通設定
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """セッション全体で使用するイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_valid_sql():
    """有効なSQLサンプル"""
    return "SELECT * FROM employees WHERE age > 25"


@pytest.fixture
def sample_invalid_sql():
    """無効なSQLサンプル"""
    return "DROP TABLE employees; DELETE FROM users;"