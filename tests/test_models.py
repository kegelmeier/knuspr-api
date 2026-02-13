from __future__ import annotations

import pytest
from pydantic import ValidationError

from knuspr.models import (
    AccountData,
    Cart,
    CartItem,
    DeliverySlot,
    Order,
    OrderProduct,
    PremiumProfile,
    SearchResult,
)


class TestSearchResult:
    def test_parse_with_dict_price(self) -> None:
        data = {
            "productId": 1001,
            "productName": "Bio Vollmilch",
            "price": {"full": 1.49, "currency": "EUR"},
            "brand": "Berchtesgadener Land",
            "textualAmount": "1 l",
            "inStock": True,
        }
        result = SearchResult.model_validate(data)
        assert result.id == 1001
        assert result.name == "Bio Vollmilch"
        assert result.price_value == 1.49
        assert result.brand == "Berchtesgadener Land"
        assert result.amount == "1 l"
        assert result.in_stock is True

    def test_parse_with_float_price(self) -> None:
        data = {
            "productId": 1002,
            "productName": "Frische Milch",
            "price": 1.29,
        }
        result = SearchResult.model_validate(data)
        assert result.price_value == 1.29

    def test_parse_with_none_price(self) -> None:
        data = {
            "productId": 1003,
            "productName": "No Price Item",
        }
        result = SearchResult.model_validate(data)
        assert result.price_value == 0.0

    def test_extra_fields_preserved(self) -> None:
        data = {
            "productId": 1001,
            "productName": "Test",
            "unknownField": "some_value",
        }
        result = SearchResult.model_validate(data)
        assert result.model_extra is not None
        assert result.model_extra["unknownField"] == "some_value"

    def test_populate_by_name(self) -> None:
        result = SearchResult(id=1, name="Test", price=1.0)
        assert result.id == 1
        assert result.name == "Test"


class TestCartItem:
    def test_parse(self) -> None:
        data = {
            "orderFieldId": "of-abc-123",
            "productId": 1001,
            "productName": "Bio Vollmilch",
            "quantity": 2,
            "price": 2.98,
            "primaryCategoryName": "Milch",
            "brand": "BGL",
        }
        item = CartItem.model_validate(data)
        assert item.order_field_id == "of-abc-123"
        assert item.product_id == 1001
        assert item.product_name == "Bio Vollmilch"
        assert item.quantity == 2
        assert item.price == 2.98


class TestCart:
    def test_empty_cart(self) -> None:
        cart = Cart()
        assert cart.total_price == 0.0
        assert cart.total_items == 0
        assert cart.can_make_order is False
        assert cart.items == []

    def test_cart_with_items(self) -> None:
        cart = Cart(
            total_price=4.27,
            total_items=2,
            can_make_order=True,
            items=[
                CartItem(
                    order_field_id="of-1",
                    product_id=1001,
                    product_name="Milk",
                    quantity=1,
                    price=1.49,
                )
            ],
        )
        assert cart.total_price == 4.27
        assert len(cart.items) == 1


class TestOrder:
    def test_parse_with_products(self) -> None:
        data = {
            "id": "ord-001",
            "orderNumber": "KN-2025-001",
            "status": "delivered",
            "totalPrice": 45.67,
            "products": [
                {"productId": 1001, "productName": "Milk", "quantity": 3, "price": 1.49}
            ],
        }
        order = Order.model_validate(data)
        assert order.id == "ord-001"
        assert order.order_number == "KN-2025-001"
        assert order.total_price == 45.67
        assert len(order.all_products) == 1

    def test_parse_with_items_fallback(self) -> None:
        data = {
            "id": "ord-002",
            "items": [{"name": "Bread", "quantity": 1, "price": 2.50}],
        }
        order = Order.model_validate(data)
        assert len(order.all_products) == 1
        assert order.all_products[0].display_name == "Bread"

    def test_all_products_prefers_products(self) -> None:
        data = {
            "id": "ord-003",
            "products": [{"productName": "A", "quantity": 1}],
            "items": [{"name": "B", "quantity": 1}],
        }
        order = Order.model_validate(data)
        assert order.all_products[0].display_name == "A"


class TestOrderProduct:
    def test_display_name_prefers_product_name(self) -> None:
        p = OrderProduct(product_name="Vollmilch", name="Milk")
        assert p.display_name == "Vollmilch"

    def test_display_name_falls_back_to_name(self) -> None:
        p = OrderProduct(name="Milk")
        assert p.display_name == "Milk"

    def test_display_name_unknown(self) -> None:
        p = OrderProduct()
        assert p.display_name == "Unknown"


class TestDeliverySlot:
    def test_defaults(self) -> None:
        slot = DeliverySlot()
        assert slot.is_available is True
        assert slot.price is None


class TestPremiumProfile:
    def test_defaults(self) -> None:
        p = PremiumProfile()
        assert p.is_premium is False
        assert p.valid_until is None


class TestAccountData:
    def test_with_nested_models(self) -> None:
        data = AccountData(
            user_id=123,
            address_id=456,
            premium=PremiumProfile(is_premium=True, valid_until="2025-12-31"),
            cart=Cart(total_price=10.0, total_items=3),
        )
        assert data.user_id == 123
        assert data.premium is not None
        assert data.premium.is_premium is True
        assert data.cart is not None
        assert data.cart.total_price == 10.0
