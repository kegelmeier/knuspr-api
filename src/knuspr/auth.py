from __future__ import annotations

import httpx

from knuspr import endpoints
from knuspr.config import KnusprConfig
from knuspr.exceptions import APIError, AuthenticationError, NetworkError


class AuthHandler:
    def __init__(self, config: KnusprConfig):
        self._config = config
        self.user_id: int | None = None
        self.address_id: int | None = None
        self._authenticated: bool = False

    def login(self, http_client: httpx.Client) -> dict:
        try:
            response = http_client.post(
                self._config.base_url + endpoints.LOGIN,
                json={
                    "email": self._config.username,
                    "password": self._config.password,
                    "name": "",
                },
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Login request failed: {e}") from e

        if response.status_code in (401, 403):
            raise AuthenticationError("Invalid credentials")

        data = response.json()
        inner_status = data.get("status")
        if inner_status and inner_status in (401, 403):
            raise AuthenticationError("Invalid credentials")

        if inner_status and inner_status not in (200, 202):
            messages = data.get("messages", [])
            msg = messages[0].get("content", "Login failed") if messages else "Login failed"
            raise APIError(msg, status_code=inner_status)

        user_data = data.get("data", {})
        self.user_id = user_data.get("user", {}).get("id")
        self.address_id = user_data.get("address", {}).get("id")
        self._authenticated = True
        return data

    def logout(self, http_client: httpx.Client) -> None:
        try:
            http_client.post(self._config.base_url + endpoints.LOGOUT)
        except httpx.RequestError:
            pass
        finally:
            self.user_id = None
            self.address_id = None
            self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated
