from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SearchResult(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: int = Field(alias="productId")
    name: str = Field(alias="productName")
    price: Any = None
    brand: str = ""
    amount: str = Field("", alias="textualAmount")
    badge: str | None = None
    favourite: bool = False
    in_stock: bool = Field(True, alias="inStock")
    image_path: str | None = Field(None, alias="imgPath")

    @property
    def price_value(self) -> float:
        if isinstance(self.price, dict):
            return float(self.price.get("full", 0))
        return float(self.price or 0)


class CartItem(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    order_field_id: str = Field(alias="orderFieldId")
    product_id: int = Field(alias="productId")
    product_name: str = Field("", alias="productName")
    quantity: int = 0
    price: float = 0.0
    primary_category_name: str = Field("", alias="primaryCategoryName")
    brand: str = ""


class Cart(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_price: float = 0.0
    total_items: int = 0
    can_make_order: bool = False
    items: list[CartItem] = []


class OrderProduct(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    product_id: str | int | None = Field(None, alias="productId")
    product_name: str | None = Field(None, alias="productName")
    name: str | None = None
    quantity: int | None = None
    price: float | None = None
    total_price: float | None = Field(None, alias="totalPrice")
    brand: str | None = None

    @property
    def display_name(self) -> str:
        return self.product_name or self.name or "Unknown"


class Order(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str | int | None = None
    order_number: str | None = Field(None, alias="orderNumber")
    status: str | None = None
    created_at: str | None = Field(None, alias="createdAt")
    delivered_at: str | None = Field(None, alias="deliveredAt")
    delivery_date: str | None = Field(None, alias="deliveryDate")
    total_price: float | None = Field(None, alias="totalPrice")
    price: float | None = None
    products: list[OrderProduct] = []
    items: list[OrderProduct] = []

    @property
    def all_products(self) -> list[OrderProduct]:
        return self.products if self.products else self.items


class DeliverySlot(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | int | None = None
    start: str | None = None
    end: str | None = None
    is_available: bool = True
    price: float | None = None


class PremiumProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    is_premium: bool = False
    valid_until: str | None = None


class AccountData(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: int | None = None
    address_id: int | None = None
    premium: PremiumProfile | None = None
    cart: Cart | None = None
