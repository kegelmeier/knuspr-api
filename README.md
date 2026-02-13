# knuspr-api

Python wrapper for the Knuspr.de grocery delivery API (unofficial).

## Installation

```bash
uv pip install -e .
```

## Configuration

```bash
export KNUSPR_USERNAME="your_email@example.com"
export KNUSPR_PASSWORD="your_password"
```

Or create a `.env` file (see `.env.example`).

## Usage

### Python library

```python
from knuspr import KnusprClient

with KnusprClient() as client:
    products = client.search_products("Bio Vollmilch", limit=5)
    for p in products:
        print(f"{p.name} - {p.price_value:.2f} EUR")

    client.add_to_cart(products[0].id, quantity=2)
    cart = client.get_cart()
    print(f"Cart: {cart.total_price:.2f} EUR ({cart.total_items} items)")
```

### CLI

```bash
knuspr search "Hafermilch" --limit 5
knuspr add 12345 --quantity 3
knuspr cart
knuspr remove <order_field_id>
knuspr slots
knuspr orders --limit 5
knuspr order <order_id>
knuspr account
```

## Disclaimer

This is an unofficial wrapper using reverse-engineered APIs. For personal use only.
