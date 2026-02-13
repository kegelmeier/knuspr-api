from __future__ import annotations

import pytest
import respx
from httpx import Response

from knuspr.auth import AuthHandler
from knuspr.config import KnusprConfig
from knuspr.exceptions import APIError, AuthenticationError

import httpx


BASE_URL = "https://www.knuspr.de"


@pytest.fixture
def config() -> KnusprConfig:
    return KnusprConfig(
        username="test@example.com",
        password="testpass",
        base_url=BASE_URL,
    )


@pytest.fixture
def auth(config: KnusprConfig) -> AuthHandler:
    return AuthHandler(config)


class TestLogin:
    @respx.mock
    def test_successful_login(self, auth: AuthHandler, login_response: dict) -> None:
        respx.post(f"{BASE_URL}/services/frontend-service/login").mock(
            return_value=Response(200, json=login_response)
        )
        with httpx.Client() as client:
            auth.login(client)

        assert auth.is_authenticated is True
        assert auth.user_id == 12345
        assert auth.address_id == 67890

    @respx.mock
    def test_login_invalid_credentials_http_401(self, auth: AuthHandler) -> None:
        respx.post(f"{BASE_URL}/services/frontend-service/login").mock(
            return_value=Response(401)
        )
        with httpx.Client() as client:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                auth.login(client)

        assert auth.is_authenticated is False

    @respx.mock
    def test_login_invalid_credentials_inner_status(
        self, auth: AuthHandler, login_error_response: dict
    ) -> None:
        respx.post(f"{BASE_URL}/services/frontend-service/login").mock(
            return_value=Response(200, json=login_error_response)
        )
        with httpx.Client() as client:
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                auth.login(client)

    @respx.mock
    def test_login_api_error(self, auth: AuthHandler) -> None:
        error_response = {
            "status": 500,
            "data": None,
            "messages": [{"type": "error", "content": "Internal server error"}],
        }
        respx.post(f"{BASE_URL}/services/frontend-service/login").mock(
            return_value=Response(200, json=error_response)
        )
        with httpx.Client() as client:
            with pytest.raises(APIError, match="Internal server error"):
                auth.login(client)


class TestLogout:
    @respx.mock
    def test_logout_clears_state(self, auth: AuthHandler, login_response: dict) -> None:
        respx.post(f"{BASE_URL}/services/frontend-service/login").mock(
            return_value=Response(200, json=login_response)
        )
        respx.post(f"{BASE_URL}/services/frontend-service/logout").mock(
            return_value=Response(200, json={"status": 200})
        )
        with httpx.Client() as client:
            auth.login(client)
            assert auth.is_authenticated is True

            auth.logout(client)
            assert auth.is_authenticated is False
            assert auth.user_id is None
            assert auth.address_id is None

    @respx.mock
    def test_logout_handles_network_error(
        self, auth: AuthHandler, login_response: dict
    ) -> None:
        respx.post(f"{BASE_URL}/services/frontend-service/login").mock(
            return_value=Response(200, json=login_response)
        )
        respx.post(f"{BASE_URL}/services/frontend-service/logout").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        with httpx.Client() as client:
            auth.login(client)
            auth.logout(client)  # should not raise
            assert auth.is_authenticated is False
