from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from knuspr.client import KnusprClient
from knuspr.exceptions import AuthenticationError, KnusprError

app = typer.Typer(name="knuspr", help="Knuspr.de grocery ordering CLI")
console = Console()


def _get_client() -> KnusprClient:
    return KnusprClient()


def _handle_error(e: Exception) -> None:
    if isinstance(e, AuthenticationError):
        console.print(
            "[red]Authentication failed. Check KNUSPR_USERNAME and KNUSPR_PASSWORD.[/red]"
        )
    elif isinstance(e, KnusprError):
        console.print(f"[red]Error: {e}[/red]")
    else:
        console.print(f"[red]Unexpected error: {e}[/red]")
    raise typer.Exit(code=1)


@app.command()
def search(query: str, limit: int = typer.Option(10, help="Max results")) -> None:
    """Search for products on Knuspr.de."""
    try:
        with _get_client() as client:
            results = client.search_products(query, limit=limit)
    except Exception as e:
        _handle_error(e)
        return

    if not results:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return

    table = Table(title=f"Search: {query}")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Price", style="green", justify="right")
    table.add_column("Amount")
    table.add_column("Brand", style="dim")
    for r in results:
        table.add_row(str(r.id), r.name, f"{r.price_value:.2f}", r.amount, r.brand)
    console.print(table)


@app.command()
def cart() -> None:
    """Show current cart contents."""
    try:
        with _get_client() as client:
            c = client.get_cart()
    except Exception as e:
        _handle_error(e)
        return

    if not c.items:
        console.print("[yellow]Cart is empty[/yellow]")
        return

    table = Table(title=f"Cart ({c.total_items} items, {c.total_price:.2f} EUR)")
    table.add_column("Field ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Qty", justify="right")
    table.add_column("Price", style="green", justify="right")
    for item in c.items:
        table.add_row(
            item.order_field_id, item.product_name, str(item.quantity), f"{item.price:.2f}"
        )
    console.print(table)


@app.command()
def add(product_id: int, quantity: int = typer.Option(1, help="Quantity to add")) -> None:
    """Add a product to cart."""
    try:
        with _get_client() as client:
            client.add_to_cart(product_id, quantity)
    except Exception as e:
        _handle_error(e)
        return

    console.print(f"[green]Added product {product_id} (qty: {quantity}) to cart[/green]")


@app.command()
def remove(order_field_id: str) -> None:
    """Remove an item from cart by its order field ID (use 'knuspr cart' to find it)."""
    try:
        with _get_client() as client:
            client.remove_from_cart(order_field_id)
    except Exception as e:
        _handle_error(e)
        return

    console.print(f"[green]Removed item {order_field_id} from cart[/green]")


@app.command()
def slots() -> None:
    """Show available delivery time slots."""
    try:
        with _get_client() as client:
            delivery_slots = client.get_delivery_slots()
    except Exception as e:
        _handle_error(e)
        return

    if not delivery_slots:
        console.print("[yellow]No delivery slots available[/yellow]")
        return

    table = Table(title="Delivery Slots")
    table.add_column("ID", style="cyan")
    table.add_column("Start")
    table.add_column("End")
    table.add_column("Available", style="green")
    table.add_column("Price", style="green", justify="right")
    for s in delivery_slots:
        avail = "Yes" if s.is_available else "No"
        price = f"{s.price:.2f}" if s.price is not None else "-"
        table.add_row(str(s.id), s.start or "-", s.end or "-", avail, price)
    console.print(table)


@app.command()
def orders(limit: int = typer.Option(10, help="Number of orders to show")) -> None:
    """Show order history."""
    try:
        with _get_client() as client:
            order_list = client.get_order_history(limit=limit)
    except Exception as e:
        _handle_error(e)
        return

    if not order_list:
        console.print("[yellow]No orders found[/yellow]")
        return

    table = Table(title="Order History")
    table.add_column("ID", style="cyan")
    table.add_column("Date")
    table.add_column("Status")
    table.add_column("Total", style="green", justify="right")
    for o in order_list:
        oid = str(o.id or o.order_number or "?")
        date = o.delivered_at or o.delivery_date or o.created_at or "-"
        total = f"{o.total_price:.2f}" if o.total_price else (f"{o.price:.2f}" if o.price else "-")
        table.add_row(oid, date, o.status or "-", total)
    console.print(table)


@app.command()
def order(order_id: str) -> None:
    """Show details for a specific order."""
    try:
        with _get_client() as client:
            o = client.get_order_detail(order_id)
    except Exception as e:
        _handle_error(e)
        return

    console.print(f"[bold]Order {o.id or o.order_number}[/bold]")
    console.print(f"Status: {o.status or 'unknown'}")
    console.print(f"Date: {o.delivered_at or o.delivery_date or o.created_at or 'unknown'}")
    total = o.total_price if o.total_price else o.price
    if total:
        console.print(f"Total: {total:.2f} EUR")

    products = o.all_products
    if products:
        table = Table(title="Products")
        table.add_column("Name")
        table.add_column("Qty", justify="right")
        table.add_column("Price", style="green", justify="right")
        for p in products:
            price = f"{p.price:.2f}" if p.price else "-"
            table.add_row(p.display_name, str(p.quantity or "?"), price)
        console.print(table)


@app.command()
def account() -> None:
    """Show account information."""
    try:
        with _get_client() as client:
            data = client.get_account_data()
    except Exception as e:
        _handle_error(e)
        return

    console.print("[bold]Account[/bold]")
    console.print(f"User ID: {data.user_id}")
    console.print(f"Address ID: {data.address_id}")
    if data.premium:
        status = "Active" if data.premium.is_premium else "Inactive"
        console.print(f"Premium: {status}")
        if data.premium.valid_until:
            console.print(f"Valid until: {data.premium.valid_until}")
    if data.cart:
        console.print(f"Cart: {data.cart.total_items} items, {data.cart.total_price:.2f} EUR")


if __name__ == "__main__":
    app()
