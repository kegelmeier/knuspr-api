from __future__ import annotations

import httpx

from knuspr import endpoints
from knuspr.auth import AuthHandler
from knuspr.config import KnusprConfig
from knuspr.exceptions import (
    APIError,
    AuthenticationError,
    KnusprError,
    NetworkError,
    RateLimitError,
)
from knuspr.models import (
    AccountData,
    Cart,
    CartItem,
    DeliverySlot,
    Order,
    PremiumProfile,
    SearchResult,
)
from knuspr.rate_limiter import RateLimiter


class KnusprClient:
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        config: KnusprConfig | None = None,
    ):
        if config:
            self._config = config
        else:
            kwargs: dict = {}
            if username:
                kwargs["username"] = username
            if password:
                kwargs["password"] = password
            self._config = KnusprConfig(**kwargs)

        self._rate_limiter = RateLimiter(self._config.min_request_interval)
        self._auth = AuthHandler(self._config)
        self._http: httpx.Client | None = None

    # --- Context Manager ---

    def __enter__(self) -> KnusprClient:
        self._http = httpx.Client(
            headers=self._default_headers(),
            timeout=self._config.request_timeout,
            follow_redirects=True,
        )
        self._auth.login(self._http)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        if self._http:
            try:
                self._auth.logout(self._http)
            finally:
                self._http.close()
                self._http = None

    # --- Internal HTTP ---

    def _ensure_client(self) -> httpx.Client:
        if self._http is None:
            raise KnusprError("Client not initialized. Use 'with KnusprClient() as client:'")
        return self._http

    def _handle_response(self, response: httpx.Response) -> dict:
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Increase min_request_interval.")
        if response.status_code in (401, 403):
            raise AuthenticationError("Session expired or invalid")
        response.raise_for_status()

        body = response.json()
        inner_status = body.get("status")
        if inner_status and isinstance(inner_status, int) and inner_status >= 400:
            messages = body.get("messages", [])
            msg = messages[0].get("content", "API error") if messages else "API error"
            raise APIError(msg, status_code=inner_status)

        return body.get("data", body)

    def _request(self, method: str, path: str, **kwargs) -> dict:  # type: ignore[no-untyped-def]
        self._rate_limiter.wait_sync()
        client = self._ensure_client()
        url = self._config.base_url + path
        try:
            response = client.request(method, url, **kwargs)
        except httpx.RequestError as e:
            raise NetworkError(f"Request to {path} failed: {e}") from e
        return self._handle_response(response)

    def _get(self, path: str, **kwargs) -> dict:  # type: ignore[no-untyped-def]
        return self._request("GET", path, **kwargs)

    def _post(self, path: str, **kwargs) -> dict:  # type: ignore[no-untyped-def]
        return self._request("POST", path, **kwargs)

    def _delete(self, path: str, **kwargs) -> dict:  # type: ignore[no-untyped-def]
        return self._request("DELETE", path, **kwargs)

    # --- Domain Methods ---

    def search_products(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for products on Knuspr.de."""
        params = {
            "search": query,
            "offset": "0",
            "limit": str(limit),
            "companyId": "1",
            "filterData": '{"filters":[]}',
            "canCorrect": "true",
        }
        data = self._get(endpoints.SEARCH, params=params)
        raw_products = data.get("productList", [])
        results = []
        for p in raw_products:
            badge = p.get("badge")
            if isinstance(badge, list) and any(
                b.get("slug") == "promoted" for b in badge if isinstance(b, dict)
            ):
                continue
            results.append(SearchResult.model_validate(p))
        return results

    def add_to_cart(self, product_id: int, quantity: int = 1) -> int:
        """Add a product to the cart. Returns the product_id."""
        payload = {
            "actionId": None,
            "productId": product_id,
            "quantity": quantity,
            "recipeId": None,
            "source": "true:Search Results",
        }
        self._post(endpoints.CART, json=payload)
        return product_id

    def get_cart(self) -> Cart:
        """Get the current cart contents."""
        data = self._get(endpoints.CART)
        items_raw = data.get("items", {})
        cart_items = []
        if isinstance(items_raw, dict):
            for product_id, item_data in items_raw.items():
                item_data["productId"] = int(product_id)
                cart_items.append(CartItem.model_validate(item_data))
        elif isinstance(items_raw, list):
            cart_items = [CartItem.model_validate(item) for item in items_raw]

        return Cart(
            total_price=data.get("totalPrice", 0.0),
            total_items=len(cart_items),
            can_make_order=data.get("canMakeOrder", False),
            items=cart_items,
        )

    def remove_from_cart(self, order_field_id: str) -> bool:
        """Remove an item from cart by its orderFieldId (from get_cart)."""
        self._delete(endpoints.CART, params={"orderFieldId": order_field_id})
        return True

    def get_delivery_slots(self) -> list[DeliverySlot]:
        """Get available delivery time slots."""
        if not self._auth.user_id or not self._auth.address_id:
            raise KnusprError("user_id and address_id required. Are you logged in?")
        params = {
            "userId": str(self._auth.user_id),
            "addressId": str(self._auth.address_id),
            "reasonableDeliveryTime": "true",
        }
        data = self._get(endpoints.TIMESLOTS, params=params)
        slots_raw = data if isinstance(data, list) else data.get("slots", [])
        return [DeliverySlot.model_validate(s) for s in slots_raw]

    def get_order_history(self, limit: int = 50, offset: int = 0) -> list[Order]:
        """Get delivered order history."""
        params = {"offset": str(offset), "limit": str(limit)}
        data = self._get(endpoints.DELIVERED_ORDERS, params=params)
        orders_raw = data if isinstance(data, list) else data.get("orders", [])
        return [Order.model_validate(o) for o in orders_raw]

    def get_order_detail(self, order_id: str) -> Order:
        """Get details for a specific order."""
        path = endpoints.ORDER_DETAIL.format(order_id=order_id)
        data = self._get(path)
        return Order.model_validate(data)

    def get_upcoming_orders(self) -> list[Order]:
        """Get upcoming (not yet delivered) orders."""
        data = self._get(endpoints.UPCOMING_ORDERS)
        orders_raw = data if isinstance(data, list) else data.get("orders", [])
        return [Order.model_validate(o) for o in orders_raw]

    def get_premium_info(self) -> PremiumProfile:
        """Get premium subscription information."""
        data = self._get(endpoints.PREMIUM_PROFILE)
        return PremiumProfile.model_validate(data)

    def get_account_data(self) -> AccountData:
        """Get aggregated account data (premium, cart)."""
        premium = self.get_premium_info()
        cart = self.get_cart()
        return AccountData(
            user_id=self._auth.user_id,
            address_id=self._auth.address_id,
            premium=premium,
            cart=cart,
        )

    # --- Headers ---

    def _default_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            "Referer": self._config.base_url,
            "Origin": self._config.base_url,
            "Accept-Language": self._config.language,
            "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
