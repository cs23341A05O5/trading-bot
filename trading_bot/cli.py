#!/usr/bin/env python3
"""CLI interface for the Binance Futures Trading Bot.

Provides command-line interface for placing orders and managing trades
on Binance Futures Testnet.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bot.config import Config, load_config
from bot.logging_config import get_logger, setup_logging
from bot.orders import OrderManager, OrderResult
from bot.validators import (
    OrderInput,
    OrderSide,
    OrderType,
    validate_cli_input,
)

# Initialize Rich console for colored output
console = Console()

# Create Typer app
app = typer.Typer(
    name="trading-bot",
    help="A production-quality trading bot for Binance Futures Testnet.",
    add_completion=False,
)

# Global variables for lazy initialization
_config: Optional[Config] = None
_order_manager: Optional[OrderManager] = None
_logger = None


def get_config() -> Config:
    """Get or initialize configuration.

    Returns:
        Config object.

    Raises:
        typer.Exit: If configuration fails to load.
    """
    global _config
    if _config is None:
        try:
            _config = load_config()
        except ValueError as e:
            console.print(f"[red]Configuration Error:[/red] {e}")
            console.print(
                "\n[yellow]Please create a .env file with your API credentials:[/yellow]"
            )
            console.print("  API_KEY=your_api_key_here")
            console.print("  API_SECRET=your_api_secret_here")
            raise typer.Exit(1)
    return _config


def get_order_manager() -> OrderManager:
    """Get or initialize order manager.

    Returns:
        OrderManager instance.
    """
    global _order_manager, _logger
    if _order_manager is None:
        from bot.client import BinanceClient

        config = get_config()

        # Setup logging
        log_dir = Path(__file__).parent / "logs"
        setup_logging(log_dir=str(log_dir))
        _logger = get_logger("cli")

        client = BinanceClient(config)
        _order_manager = OrderManager(client)
    return _order_manager


def print_order_summary(order_input: OrderInput) -> None:
    """Print order summary before placement.

    Args:
        order_input: Validated order input.
    """
    table = Table(title="Order Summary", show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Symbol", order_input.symbol)
    table.add_row("Side", order_input.side.value)
    table.add_row("Type", order_input.order_type.value)
    table.add_row("Quantity", f"{order_input.quantity}")

    if order_input.price is not None:
        table.add_row("Price", f"{order_input.price}")

    if order_input.stop_price is not None:
        table.add_row("Stop Price", f"{order_input.stop_price}")

    console.print(table)


def print_order_result(result: OrderResult) -> None:
    """Print order result after placement.

    Args:
        result: Order result from placement attempt.
    """
    if result.success:
        # Success panel
        console.print()
        console.print(
            Panel(
                "[bold green]✓ ORDER SUCCESS[/bold green]",
                title="Result",
                border_style="green",
            )
        )

        # Response details table
        table = Table(title="Response", show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        if result.order_id:
            table.add_row("OrderID", str(result.order_id))

        if result.symbol:
            table.add_row("Symbol", result.symbol)

        if result.status:
            table.add_row("Status", result.status)

        if result.executed_qty is not None:
            table.add_row("ExecutedQty", f"{result.executed_qty}")

        if result.avg_price is not None:
            table.add_row("AvgPrice", f"{result.avg_price:.2f}")

        console.print(table)
        console.print()

    else:
        # Failure panel
        console.print()
        console.print(
            Panel(
                f"[bold red]✗ ORDER FAILED[/bold red]\n\n{result.message}",
                title="Error",
                border_style="red",
            )
        )
        console.print()


def print_error(message: str) -> None:
    """Print error message.

    Args:
        message: Error message to display.
    """
    console.print(f"\n[red]Error:[/red] {message}\n")


def print_success(message: str) -> None:
    """Print success message.

    Args:
        message: Success message to display.
    """
    console.print(f"\n[green]✓[/green] {message}\n")


def print_info(message: str) -> None:
    """Print info message.

    Args:
        message: Info message to display.
    """
    console.print(f"\n[cyan]ℹ[/cyan] {message}\n")


@app.command()
def place(
    symbol: str = typer.Option(
        ...,
        "--symbol", "-s",
        help="Trading pair symbol (e.g., BTCUSDT)",
    ),
    side: str = typer.Option(
        ...,
        "--side",
        help="Order side: BUY or SELL",
    ),
    type: str = typer.Option(
        ...,
        "--type", "-t",
        help="Order type: MARKET, LIMIT, or STOP_LIMIT",
    ),
    quantity: float = typer.Option(
        ...,
        "--quantity", "-q",
        help="Order quantity",
        min=0.000001,
    ),
    price: Optional[float] = typer.Option(
        None,
        "--price", "-p",
        help="Limit price (required for LIMIT and STOP_LIMIT orders)",
    ),
    stop_price: Optional[float] = typer.Option(
        None,
        "--stop-price",
        help="Stop price (required for STOP_LIMIT orders)",
    ),
    leverage: Optional[int] = typer.Option(
        None,
        "--leverage", "-l",
        help="Leverage to set before placing order (1-125)",
        min=1,
        max=125,
    ),
    confirm: bool = typer.Option(
        True,
        "--confirm/--no-confirm",
        help="Ask for confirmation before placing order",
    ),
) -> None:
    """Place a new order on Binance Futures Testnet.

    Examples:
        python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

        python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000
    """
    # Validate input
    order_input, error = validate_cli_input(
        symbol=symbol,
        side=side,
        order_type=type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    if error:
        print_error(error)
        raise typer.Exit(1)

    # Print order summary
    console.print()
    print_order_summary(order_input)

    # Ask for confirmation
    if confirm:
        proceed = typer.confirm("\nProceed with order placement?")
        if not proceed:
            console.print("\n[yellow]Order cancelled by user.[/yellow]\n")
            raise typer.Exit(0)

    # Initialize order manager
    try:
        order_manager = get_order_manager()
    except Exception as e:
        print_error(f"Failed to initialize: {e}")
        raise typer.Exit(1)

    # Set leverage if specified
    if leverage:
        result = order_manager.set_leverage(order_input.symbol, leverage)
        if result.get("success"):
            console.print(f"[dim]Leverage set to {leverage}x[/dim]")
        else:
            console.print(
                f"[yellow]Warning: Could not set leverage: {result.get('error')}[/yellow]"
            )

    # Place order
    result = order_manager.place_order(order_input)

    # Print result
    print_order_result(result)

    # Log the result
    if _logger:
        if result.success:
            _logger.info(
                f"Order placed: ID={result.order_id}, Symbol={result.symbol}, "
                f"Status={result.status}"
            )
        else:
            _logger.error(f"Order failed: {result.message}")

    # Exit with appropriate code
    raise typer.Exit(0 if result.success else 1)


@app.command()
def cancel(
    symbol: str = typer.Option(
        ...,
        "--symbol", "-s",
        help="Trading pair symbol",
    ),
    order_id: int = typer.Option(
        ...,
        "--order-id", "-o",
        help="Order ID to cancel",
    ),
) -> None:
    """Cancel an existing order.

    Example:
        python cli.py cancel --symbol BTCUSDT --order-id 12345
    """
    try:
        order_manager = get_order_manager()
    except Exception as e:
        print_error(f"Failed to initialize: {e}")
        raise typer.Exit(1)

    console.print(
        f"\n[cyan]Cancelling order {order_id} for {symbol.upper()}...[/cyan]\n"
    )

    result = order_manager.cancel_order(symbol.upper(), order_id)
    print_order_result(result)

    raise typer.Exit(0 if result.success else 1)


@app.command()
def orders(
    symbol: Optional[str] = typer.Option(
        None,
        "--symbol", "-s",
        help="Filter by trading pair symbol",
    ),
) -> None:
    """List all open orders.

    Example:
        python cli.py orders --symbol BTCUSDT
    """
    try:
        order_manager = get_order_manager()
    except Exception as e:
        print_error(f"Failed to initialize: {e}")
        raise typer.Exit(1)

    result = order_manager.get_open_orders(symbol)

    if not result.get("success"):
        print_error(result.get("error", "Failed to get orders"))
        raise typer.Exit(1)

    orders_list = result.get("orders", [])

    if not orders_list:
        console.print("\n[yellow]No open orders found.[/yellow]\n")
        raise typer.Exit(0)

    # Create orders table
    table = Table(title="Open Orders")
    table.add_column("Order ID", style="cyan")
    table.add_column("Symbol", style="green")
    table.add_column("Side", style="yellow")
    table.add_column("Type", style="blue")
    table.add_column("Quantity", style="magenta")
    table.add_column("Price", style="red")
    table.add_column("Status", style="white")

    for order in orders_list:
        table.add_row(
            str(order.get("orderId")),
            order.get("symbol", ""),
            order.get("side", ""),
            order.get("type", ""),
            str(order.get("origQty", "")),
            str(order.get("price", "")),
            order.get("status", ""),
        )

    console.print(table)
    raise typer.Exit(0)


@app.command()
def balance(
    asset: str = typer.Option(
        "USDT",
        "--asset", "-a",
        help="Asset to check balance for",
    ),
) -> None:
    """Check account balance.

    Example:
        python cli.py balance --asset USDT
    """
    try:
        order_manager = get_order_manager()
    except Exception as e:
        print_error(f"Failed to initialize: {e}")
        raise typer.Exit(1)

    result = order_manager.get_account_balance(asset)

    if not result.get("success"):
        print_error(result.get("error", "Failed to get balance"))
        raise typer.Exit(1)

    # Create balance table
    table = Table(title=f"Balance: {asset}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Asset", result.get("asset", ""))
    table.add_row("Available", f"{result.get('available', 0):.4f}")
    table.add_row("Total", f"{result.get('total', 0):.4f}")

    console.print(table)
    raise typer.Exit(0)


@app.command()
def leverage(
    symbol: str = typer.Option(
        ...,
        "--symbol", "-s",
        help="Trading pair symbol",
    ),
    leverage_value: int = typer.Argument(
        ...,
        help="Leverage value (1-125)",
        min=1,
        max=125,
    ),
) -> None:
    """Set leverage for a symbol.

    Example:
        python cli.py leverage BTCUSDT 10
    """
    try:
        order_manager = get_order_manager()
    except Exception as e:
        print_error(f"Failed to initialize: {e}")
        raise typer.Exit(1)

    result = order_manager.set_leverage(symbol.upper(), leverage_value)

    if result.get("success"):
        print_success(
            result.get("message", f"Leverage set to {leverage_value}x for {symbol.upper()}")
        )
    else:
        print_error(result.get("error", "Failed to set leverage"))

    raise typer.Exit(0 if result.get("success") else 1)


@app.command()
def test() -> None:
    """Test API connection and authentication.

    Example:
        python cli.py test
    """
    console.print("\n[cyan]Testing API connection...[/cyan]\n")

    try:
        from bot.client import BinanceClient

        config = get_config()
        client = BinanceClient(config)

        # Test connection
        if client.test_connection():
            print_success("API connection successful!")

            # Show account info
            balance_result = client.get_balance("USDT")
            console.print(
                f"[dim]USDT Balance: {balance_result.get('availableBalance', 'N/A')}[/dim]"
            )
        else:
            print_error("API connection failed. Check your credentials.")
            raise typer.Exit(1)

    except Exception as e:
        print_error(f"Connection test failed: {e}")
        raise typer.Exit(1)


@app.command()
def position(
    symbol: Optional[str] = typer.Option(
        None,
        "--symbol", "-s",
        help="Filter by trading pair symbol",
    ),
) -> None:
    """View current positions.

    Example:
        python cli.py position --symbol BTCUSDT
    """
    try:
        from bot.client import BinanceClient

        config = get_config()
        client = BinanceClient(config)

        positions = client.get_position_info(symbol)

        # Filter out zero positions
        active_positions = [
            p for p in positions
            if float(p.get("positionAmt", 0)) != 0
        ]

        if not active_positions:
            console.print("\n[yellow]No active positions found.[/yellow]\n")
            raise typer.Exit(0)

        table = Table(title="Active Positions")
        table.add_column("Symbol", style="cyan")
        table.add_column("Side", style="yellow")
        table.add_column("Size", style="green")
        table.add_column("Entry Price", style="blue")
        table.add_column("Mark Price", style="magenta")
        table.add_column("Unrealized PnL", style="red")
        table.add_column("Leverage", style="white")

        for pos in active_positions:
            pos_amt = float(pos.get("positionAmt", 0))
            side = "LONG" if pos_amt > 0 else "SHORT"
            unrealized_pnl = float(pos.get("unRealizedProfit", 0))
            pnl_color = "green" if unrealized_pnl >= 0 else "red"

            table.add_row(
                pos.get("symbol", ""),
                side,
                str(abs(pos_amt)),
                f"{float(pos.get('entryPrice', 0)):.4f}",
                f"{float(pos.get('markPrice', 0)):.4f}",
                f"[{pnl_color}]{unrealized_pnl:.4f}[/{pnl_color}]",
                f"{pos.get('leverage', '1')}x",
            )

        console.print(table)
        raise typer.Exit(0)

    except Exception as e:
        print_error(f"Failed to get positions: {e}")
        raise typer.Exit(1)


@app.command()
def history(
    symbol: Optional[str] = typer.Option(
        None,
        "--symbol", "-s",
        help="Filter by trading pair symbol",
    ),
    limit: int = typer.Option(
        10,
        "--limit", "-l",
        help="Number of orders to show",
        min=1,
        max=100,
    ),
) -> None:
    """View order history (recent orders).

    Example:
        python cli.py history --symbol BTCUSDT --limit 5
    """
    try:
        from bot.client import BinanceClient

        config = get_config()
        client = BinanceClient(config)

        # Get all orders (open + closed)
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol.upper()

        response = client._make_request("GET", "/fapi/v1/allOrders", params, signed=True)

        if not response:
            console.print("\n[yellow]No order history found.[/yellow]\n")
            raise typer.Exit(0)

        table = Table(title=f"Order History (Last {len(response)} orders)")
        table.add_column("Order ID", style="cyan")
        table.add_column("Symbol", style="green")
        table.add_column("Side", style="yellow")
        table.add_column("Type", style="blue")
        table.add_column("Qty", style="magenta")
        table.add_column("Price", style="red")
        table.add_column("Status", style="white")
        table.add_column("Time", style="dim")

        for order in response:
            # Format timestamp
            import time
            timestamp = order.get("time", 0)
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp / 1000))

            # Color status
            status = order.get("status", "")
            if status == "FILLED":
                status_display = f"[green]{status}[/green]"
            elif status == "CANCELED":
                status_display = f"[yellow]{status}[/yellow]"
            elif status == "NEW":
                status_display = f"[blue]{status}[/blue]"
            else:
                status_display = status

            table.add_row(
                str(order.get("orderId")),
                order.get("symbol", ""),
                order.get("side", ""),
                order.get("type", ""),
                str(order.get("origQty", "")),
                str(order.get("price", "")) if float(order.get("price", 0)) > 0 else "MARKET",
                status_display,
                time_str,
            )

        console.print(table)
        raise typer.Exit(0)

    except Exception as e:
        print_error(f"Failed to get order history: {e}")
        raise typer.Exit(1)


@app.command()
def interactive() -> None:
    """Launch interactive CLI menu.

    Example:
        python cli.py interactive
    """
    console.print(
        Panel(
            "[bold cyan]Binance Futures Trading Bot[/bold cyan]\n"
            "[dim]Interactive Mode[/dim]",
            border_style="cyan",
        )
    )

    while True:
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("  1. Place Market Order")
        console.print("  2. Place Limit Order")
        console.print("  3. Place Stop-Limit Order")
        console.print("  4. View Open Orders")
        console.print("  5. View Order History")
        console.print("  6. View Positions")
        console.print("  7. Check Balance")
        console.print("  8. Set Leverage")
        console.print("  9. Cancel Order")
        console.print("  10. Test Connection")
        console.print("  0. Exit")

        choice = typer.prompt("\nSelect option", type=int, default=0)

        if choice == 0:
            console.print("\n[yellow]Goodbye![/yellow]\n")
            break

        elif choice == 1:
            # Market order
            symbol = typer.prompt("Symbol (e.g., BTCUSDT)")
            side = typer.prompt("Side (BUY/SELL)")
            quantity = typer.prompt("Quantity", type=float)

            order_input, error = validate_cli_input(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
            )

            if error:
                print_error(error)
                continue

            print_order_summary(order_input)
            if typer.confirm("Place order?"):
                order_manager = get_order_manager()
                result = order_manager.place_order(order_input)
                print_order_result(result)

        elif choice == 2:
            # Limit order
            symbol = typer.prompt("Symbol (e.g., BTCUSDT)")
            side = typer.prompt("Side (BUY/SELL)")
            quantity = typer.prompt("Quantity", type=float)
            price = typer.prompt("Price", type=float)

            order_input, error = validate_cli_input(
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
            )

            if error:
                print_error(error)
                continue

            print_order_summary(order_input)
            if typer.confirm("Place order?"):
                order_manager = get_order_manager()
                result = order_manager.place_order(order_input)
                print_order_result(result)

        elif choice == 3:
            # Stop-limit order
            symbol = typer.prompt("Symbol (e.g., BTCUSDT)")
            side = typer.prompt("Side (BUY/SELL)")
            quantity = typer.prompt("Quantity", type=float)
            price = typer.prompt("Limit Price", type=float)
            stop_price = typer.prompt("Stop Price", type=float)

            order_input, error = validate_cli_input(
                symbol=symbol,
                side=side,
                order_type="STOP_LIMIT",
                quantity=quantity,
                price=price,
                stop_price=stop_price,
            )

            if error:
                print_error(error)
                continue

            print_order_summary(order_input)
            if typer.confirm("Place order?"):
                order_manager = get_order_manager()
                result = order_manager.place_order(order_input)
                print_order_result(result)

        elif choice == 4:
            # View open orders
            symbol = typer.prompt("Symbol (leave empty for all)", default="")
            order_manager = get_order_manager()
            result = order_manager.get_open_orders(symbol if symbol else None)

            if result.get("success"):
                orders_list = result.get("orders", [])
                if not orders_list:
                    console.print("\n[yellow]No open orders found.[/yellow]")
                else:
                    table = Table(title="Open Orders")
                    table.add_column("Order ID", style="cyan")
                    table.add_column("Symbol", style="green")
                    table.add_column("Side", style="yellow")
                    table.add_column("Type", style="blue")
                    table.add_column("Qty", style="magenta")
                    table.add_column("Price", style="red")

                    for order in orders_list:
                        table.add_row(
                            str(order.get("orderId")),
                            order.get("symbol", ""),
                            order.get("side", ""),
                            order.get("type", ""),
                            str(order.get("origQty", "")),
                            str(order.get("price", "")),
                        )
                    console.print(table)
            else:
                print_error(result.get("error", "Failed to get orders"))

        elif choice == 5:
            # View order history
            symbol = typer.prompt("Symbol (leave empty for all)", default="")
            limit = typer.prompt("Number of orders", type=int, default=10)
            from bot.client import BinanceClient
            config = get_config()
            client = BinanceClient(config)
            params = {"limit": limit}
            if symbol:
                params["symbol"] = symbol.upper()
            response = client._make_request("GET", "/fapi/v1/allOrders", params, signed=True)
            if response:
                table = Table(title=f"Order History (Last {len(response)} orders)")
                table.add_column("Order ID", style="cyan")
                table.add_column("Symbol", style="green")
                table.add_column("Side", style="yellow")
                table.add_column("Type", style="blue")
                table.add_column("Qty", style="magenta")
                table.add_column("Status", style="red")
                for order in response:
                    table.add_row(
                        str(order.get("orderId")),
                        order.get("symbol", ""),
                        order.get("side", ""),
                        order.get("type", ""),
                        str(order.get("origQty", "")),
                        order.get("status", ""),
                    )
                console.print(table)
            else:
                console.print("\n[yellow]No order history found.[/yellow]")

        elif choice == 6:
            # View positions
            from bot.client import BinanceClient
            config = get_config()
            client = BinanceClient(config)
            positions = client.get_position_info()
            active_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
            if not active_positions:
                console.print("\n[yellow]No active positions found.[/yellow]")
            else:
                table = Table(title="Active Positions")
                table.add_column("Symbol", style="cyan")
                table.add_column("Side", style="yellow")
                table.add_column("Size", style="green")
                table.add_column("Entry Price", style="blue")
                table.add_column("Unrealized PnL", style="red")
                for pos in active_positions:
                    pos_amt = float(pos.get("positionAmt", 0))
                    side = "LONG" if pos_amt > 0 else "SHORT"
                    table.add_row(
                        pos.get("symbol", ""),
                        side,
                        str(abs(pos_amt)),
                        f"{float(pos.get('entryPrice', 0)):.4f}",
                        f"{float(pos.get('unRealizedProfit', 0)):.4f}",
                    )
                console.print(table)

        elif choice == 7:
            # Check balance
            asset = typer.prompt("Asset", default="USDT")
            order_manager = get_order_manager()
            result = order_manager.get_account_balance(asset)

            if result.get("success"):
                console.print(
                    f"\n[green]{asset} Balance:[/green]\n"
                    f"  Available: {result.get('available', 0):.4f}\n"
                    f"  Total: {result.get('total', 0):.4f}\n"
                )
            else:
                print_error(result.get("error", "Failed to get balance"))

        elif choice == 8:
            # Set leverage
            symbol = typer.prompt("Symbol (e.g., BTCUSDT)")
            leverage_val = typer.prompt("Leverage (1-125)", type=int, min=1, max=125)
            order_manager = get_order_manager()
            result = order_manager.set_leverage(symbol.upper(), leverage_val)

            if result.get("success"):
                print_success(f"Leverage set to {leverage_val}x for {symbol.upper()}")
            else:
                print_error(result.get("error", "Failed to set leverage"))

        elif choice == 9:
            # Cancel order
            symbol = typer.prompt("Symbol (e.g., BTCUSDT)")
            order_id = typer.prompt("Order ID", type=int)
            order_manager = get_order_manager()
            result = order_manager.cancel_order(symbol.upper(), order_id)
            print_order_result(result)

        elif choice == 10:
            # Test connection
            test()

        else:
            print_error("Invalid option. Please try again.")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
