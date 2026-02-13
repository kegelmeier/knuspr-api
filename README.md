# knuspr-api

[![PyPI](https://img.shields.io/pypi/v/knuspr-api)](https://pypi.org/project/knuspr-api/)
[![CI](https://github.com/kegelmeier/knuspr-api/actions/workflows/ci.yml/badge.svg)](https://github.com/kegelmeier/knuspr-api/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/knuspr-api)](https://pypi.org/project/knuspr-api/)
[![License](https://img.shields.io/pypi/l/knuspr-api)](https://github.com/kegelmeier/knuspr-api/blob/main/LICENSE)

Unofficial Python wrapper for the [Knuspr.de](https://www.knuspr.de) grocery delivery API.
Search products, manage your cart, check delivery slots, and view orders — from Python or the command line.

> **Note:** Knuspr is the German brand of the [Rohlik Group](https://www.rohlik.group/), which also operates Rohlik.cz, Gurkerl.at, Kifli.hu, and Sezamo.ro. This library targets the German Knuspr.de endpoint.

## Features

- **Product search** with automatic promoted-item filtering
- **Cart management** — add items, view cart, remove by order field ID
- **Delivery slots** — check available time windows
- **Order history** — list past orders and view details
- **Upcoming orders** — see scheduled deliveries
- **Premium info** — check subscription status
- **Account data** — aggregated view of your account
- **CLI** with 8 commands and rich terminal output
- **Cookie-based auth** with automatic login/logout via context manager
- **Rate limiting** — configurable minimum interval between requests (default 100ms)
- **Pydantic v2 models** with full type annotations (PEP 561)

## Installation

From PyPI:

```bash
pip install knuspr-api
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv add knuspr-api
```

From source:

```bash
git clone https://github.com/kegelmeier/knuspr-api.git
cd knuspr-api
uv pip install -e ".[dev]"
```

## Quick Start

Set your Knuspr.de credentials:

```bash
export KNUSPR_USERNAME="your_email@example.com"
export KNUSPR_PASSWORD="your_password"
```

Or create a `.env` file (see `.env.example`).

```python
from knuspr import KnusprClient

with KnusprClient() as client:
    # Search for products
    products = client.search_products("Bio Vollmilch", limit=5)
    for p in products:
        print(f"{p.name} - {p.price_value:.2f} EUR")

    # Add the first result to your cart
    client.add_to_cart(products[0].id, quantity=2)

    # Check your cart
    cart = client.get_cart()
    print(f"Cart: {cart.total_price:.2f} EUR ({cart.total_items} items)")
```

## Configuration

All settings can be provided via environment variables (prefix `KNUSPR_`) or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `KNUSPR_USERNAME` | *(required)* | Your Knuspr.de email |
| `KNUSPR_PASSWORD` | *(required)* | Your Knuspr.de password |
| `KNUSPR_BASE_URL` | `https://www.knuspr.de` | API base URL |
| `KNUSPR_MIN_REQUEST_INTERVAL` | `0.1` | Minimum seconds between requests |
| `KNUSPR_REQUEST_TIMEOUT` | `10.0` | HTTP request timeout in seconds |
| `KNUSPR_DEBUG` | `false` | Enable debug mode |

You can also pass credentials directly:

```python
with KnusprClient(username="me@example.com", password="secret") as client:
    ...
```

## CLI Reference

The `knuspr` command provides 8 subcommands with rich terminal output:

```bash
# Search products
knuspr search "Hafermilch" --limit 5

# Add a product to your cart (by product ID)
knuspr add 12345 --quantity 3

# View your cart
knuspr cart

# Remove an item from your cart (by order field ID from cart output)
knuspr remove <order_field_id>

# Check delivery time slots
knuspr slots

# View order history
knuspr orders --limit 10

# View a specific order's details
knuspr order <order_id>

# View account overview
knuspr account
```

## Python API

### `KnusprClient`

Use as a context manager for automatic login and logout:

```python
with KnusprClient() as client:
    ...
```

#### Methods

| Method | Returns | Description |
|---|---|---|
| `search_products(query, limit=10)` | `list[SearchResult]` | Search for products |
| `add_to_cart(product_id, quantity=1)` | `int` | Add a product to the cart |
| `get_cart()` | `Cart` | Get current cart contents |
| `remove_from_cart(order_field_id)` | `bool` | Remove an item by its order field ID |
| `get_delivery_slots()` | `list[DeliverySlot]` | Get available delivery windows |
| `get_order_history(limit=50, offset=0)` | `list[Order]` | Get past delivered orders |
| `get_order_detail(order_id)` | `Order` | Get details for a specific order |
| `get_upcoming_orders()` | `list[Order]` | Get scheduled upcoming orders |
| `get_premium_info()` | `PremiumProfile` | Get premium subscription info |
| `get_account_data()` | `AccountData` | Get aggregated account overview |

### Models

All models use Pydantic v2 with `extra="allow"` to handle unexpected API fields gracefully.

- **`SearchResult`** — Product from search: `id`, `name`, `price_value`, `brand`, `amount`, `in_stock`, `image_path`
- **`Cart`** — Cart state: `total_price`, `total_items`, `can_make_order`, `items`
- **`CartItem`** — Item in cart: `order_field_id`, `product_id`, `product_name`, `quantity`, `price`, `brand`
- **`Order`** — Order summary: `id`, `status`, `created_at`, `total_price`, `all_products`
- **`OrderProduct`** — Product within an order: `product_id`, `display_name`, `quantity`, `price`
- **`DeliverySlot`** — Time window: `id`, `start`, `end`, `is_available`, `price`
- **`PremiumProfile`** — Subscription: `is_premium`, `valid_until`
- **`AccountData`** — Aggregated: `user_id`, `address_id`, `premium`, `cart`

### Exceptions

```python
from knuspr import KnusprError, AuthenticationError, RateLimitError, APIError, NetworkError
```

| Exception | When |
|---|---|
| `KnusprError` | Base exception for all errors |
| `AuthenticationError` | Login failed or session expired |
| `RateLimitError` | HTTP 429 — too many requests |
| `APIError` | API returned an error status |
| `NetworkError` | Connection or timeout failure |

## Disclaimer

This is an **unofficial** library using reverse-engineered API endpoints. It is not affiliated with, endorsed by, or connected to [Rohlik Group](https://www.rohlik.group/) or Knuspr GmbH in any way.

- The API may change without notice, which could break this library.
- Use at your own risk and for **personal use only**.
- Please respect Knuspr's terms of service and rate limits.

## Contributing

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/ tests/

# Run type checker
mypy src/
```

## License

MIT License. See [LICENSE](LICENSE) for details.
