from __future__ import annotations

import json
from pathlib import Path

import pytest

from knuspr.config import KnusprConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


@pytest.fixture
def login_response() -> dict:
    return load_fixture("login_response.json")


@pytest.fixture
def login_error_response() -> dict:
    return load_fixture("login_error_response.json")


@pytest.fixture
def search_response() -> dict:
    return load_fixture("search_response.json")


@pytest.fixture
def cart_response() -> dict:
    return load_fixture("cart_response.json")


@pytest.fixture
def order_history_response() -> dict:
    return load_fixture("order_history_response.json")


@pytest.fixture
def test_config() -> KnusprConfig:
    return KnusprConfig(
        username="test@example.com",
        password="testpassword",
        base_url="https://www.knuspr.de",
    )
