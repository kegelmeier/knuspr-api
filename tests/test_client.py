from __future__ import annotations

import pytest
import respx
from httpx import Response

from knuspr.client import KnusprClient
from knuspr.config import KnusprConfig
from knuspr.exceptions import AuthenticationError, KnusprError, RateLimitError

BASE_URL = "https://www.knuspr.de"

LOGIN_SUCCESS = {
    "status": 200,
    "data": {
        "user": {"id": 12345},
        "address": {"id": 67890},
    },
    "messages": [],
}

LOGOUT_SUCCESS = {"status": 200}


@pytest.fixture
def config() -> KnusprConfig:
    return KnusprConfig(
        username="test@example.com",
        password="testpass",
        base_url=BASE_URL,
        min_request_interval=0.0,  # disable rate limiting in tests
    )


def _mock_login_logout() -> None:
    respx.post(f"{BASE_URL}/services/frontend-service/login").mock(
        return_value=Response(200, json=LOGIN_SUCCESS)
    )
    respx.post(f"{BASE_URL}/services/frontend-service/logout").mock(
        return_value=Response(200, json=LOGOUT_SUCCESS)
    )


class TestClientContextManager:
    @respx.mock
    def test_context_manager_logs_in_and_out(self, config: KnusprConfig) -> None:
        _mock_login_logout()
        with KnusprClient(config=config) as client:
            assert client._auth.is_authenticated is True
        assert client._auth.is_authenticated is False

    def test_client_not_initialized_raises(self, config: KnusprConfig) -> None:
        client = KnusprClient(config=config)
        with pytest.raises(KnusprError, match="Client not initialized"):
            client.search_products("test")


class TestSearchProducts:
    @respx.mock
    def test_search_returns_results(
        self, config: KnusprConfig, search_response: dict
    ) -> None:
        _mock_login_logout()
        respx.get(f"{BASE_URL}/services/frontend-service/search-metadata").mock(
            return_value=Response(200, json=search_response)
        )

        with KnusprClient(config=config) as client:
            results = client.search_products("Milch", limit=10)

        assert len(results) == 2  # promoted item filtered out
        assert results[0].id == 1001
        assert results[0].name == "Bio Vollmilch 3,5%"
        assert results[0].price_value == 1.49
        assert results[1].id == 1002
        assert results[1].price_value == 1.29

    @respx.mock
    def test_search_empty_results(self, config: KnusprConfig) -> None:
        _mock_login_logout()
        empty_response = {"status": 200, "data": {"productList": [], "totalCount": 0}}
        respx.get(f"{BASE_URL}/services/frontend-service/search-metadata").mock(
            return_value=Response(200, json=empty_response)
        )

        with KnusprClient(config=config) as client:
            results = client.search_products("nonexistent")

        assert results == []


class TestCartOperations:
    @respx.mock
    def test_get_cart(self, config: KnusprConfig, cart_response: dict) -> None:
        _mock_login_logout()
        respx.get(f"{BASE_URL}/services/frontend-service/v2/cart").mock(
            return_value=Response(200, json=cart_response)
        )

        with KnusprClient(config=config) as client:
            cart = client.get_cart()

        assert cart.total_price == 4.27
        assert cart.total_items == 2
        assert cart.can_make_order is True
        assert cart.items[0].order_field_id == "of-abc-123"
        assert cart.items[0].product_id == 1001
        assert cart.items[1].product_id == 1002

    @respx.mock
    def test_add_to_cart(self, config: KnusprConfig) -> None:
        _mock_login_logout()
        respx.post(f"{BASE_URL}/services/frontend-service/v2/cart").mock(
            return_value=Response(200, json={"status": 200, "data": {}})
        )

        with KnusprClient(config=config) as client:
            result = client.add_to_cart(1001, quantity=2)

        assert result == 1001

    @respx.mock
    def test_remove_from_cart(self, config: KnusprConfig) -> None:
        _mock_login_logout()
        respx.delete(f"{BASE_URL}/services/frontend-service/v2/cart").mock(
            return_value=Response(200, json={"status": 200, "data": {}})
        )

        with KnusprClient(config=config) as client:
            result = client.remove_from_cart("of-abc-123")

        assert result is True


class TestOrderOperations:
    @respx.mock
    def test_get_order_history(
        self, config: KnusprConfig, order_history_response: dict
    ) -> None:
        _mock_login_logout()
        respx.get(f"{BASE_URL}/api/v3/orders/delivered").mock(
            return_value=Response(200, json=order_history_response)
        )

        with KnusprClient(config=config) as client:
            orders = client.get_order_history(limit=10)

        assert len(orders) == 2
        assert orders[0].id == "ord-001"
        assert orders[0].order_number == "KN-2025-001"
        assert orders[0].total_price == 45.67
        assert len(orders[0].all_products) == 1

    @respx.mock
    def test_get_order_detail(self, config: KnusprConfig) -> None:
        _mock_login_logout()
        detail_response = {
            "status": 200,
            "data": {
                "id": "ord-001",
                "orderNumber": "KN-2025-001",
                "status": "delivered",
                "totalPrice": 45.67,
                "products": [
                    {
                        "productId": 1001,
                        "productName": "Bio Vollmilch",
                        "quantity": 3,
                        "price": 1.49,
                    }
                ],
            },
        }
        respx.get(f"{BASE_URL}/api/v3/orders/ord-001").mock(
            return_value=Response(200, json=detail_response)
        )

        with KnusprClient(config=config) as client:
            order = client.get_order_detail("ord-001")

        assert order.id == "ord-001"
        assert len(order.all_products) == 1
        assert order.all_products[0].display_name == "Bio Vollmilch"


class TestErrorHandling:
    @respx.mock
    def test_rate_limit_error(self, config: KnusprConfig) -> None:
        _mock_login_logout()
        respx.get(f"{BASE_URL}/services/frontend-service/search-metadata").mock(
            return_value=Response(429)
        )

        with KnusprClient(config=config) as client, pytest.raises(RateLimitError):
            client.search_products("test")

    @respx.mock
    def test_session_expired(self, config: KnusprConfig) -> None:
        _mock_login_logout()
        respx.get(f"{BASE_URL}/services/frontend-service/search-metadata").mock(
            return_value=Response(401)
        )

        with KnusprClient(config=config) as client, pytest.raises(AuthenticationError):
            client.search_products("test")
