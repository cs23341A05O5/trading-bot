"""Order management module for the trading bot.

Provides high-level order placement and management functions.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import get_logger
from bot.validators import OrderInput, OrderType

logger = get_logger("orders")


@dataclass
class OrderResult:
    """Result of an order placement attempt.

    Attributes:
        success: Whether the order was placed successfully.
        order_id: Order ID from Binance (if successful).
        symbol: Trading pair symbol.
        status: Order status.
        executed_qty: Executed quantity.
        avg_price: Average execution price.
        message: Result message.
        raw_response: Raw API response.
    """

    success: bool
    order_id: Optional[int] = None
    symbol: Optional[str] = None
    status: Optional[str] = None
    executed_qty: Optional[float] = None
    avg_price: Optional[float] = None
    message: str = ""
    raw_response: Optional[Dict[str, Any]] = None


class OrderManager:
    """Manages order placement and tracking.

    Provides high-level methods for placing and managing orders
    with proper error handling and logging.
    """

    def __init__(self, client: BinanceClient):
        """Initialize OrderManager.

        Args:
            client: BinanceClient instance for API calls.
        """
        self.client = client
        logger.info("OrderManager initialized")

    def place_order(self, order_input: OrderInput) -> OrderResult:
        """Place an order based on validated input.

        Args:
            order_input: Validated order input.

        Returns:
            OrderResult with order details or error information.
        """
        logger.info(
            f"Placing order: {order_input.side.value} {order_input.quantity} "
            f"{order_input.symbol} @ {order_input.order_type.value}"
        )

        try:
            # Map order type to Binance API format
            order_type_map = {
                OrderType.MARKET: "MARKET",
                OrderType.LIMIT: "LIMIT",
                OrderType.STOP_LIMIT: "STOP",
            }

            binance_order_type = order_type_map.get(order_input.order_type)
            if not binance_order_type:
                return OrderResult(
                    success=False,
                    message=f"Unsupported order type: {order_input.order_type.value}",
                )

            # Place the order
            response = self.client.place_order(
                symbol=order_input.symbol,
                side=order_input.side.value,
                order_type=binance_order_type,
                quantity=order_input.quantity,
                price=order_input.price,
                stop_price=order_input.stop_price,
            )

            # Parse response
            order_id = response.get("orderId")
            status = response.get("status", "UNKNOWN")
            executed_qty = float(response.get("executedQty", 0))
            avg_price = response.get("avgPrice")

            # Calculate average price if not provided
            if not avg_price and executed_qty > 0:
                cum_quote = float(response.get("cumQuote", 0))
                if cum_quote > 0:
                    avg_price = cum_quote / executed_qty

            logger.info(
                f"Order placed successfully: ID={order_id}, Status={status}, "
                f"ExecutedQty={executed_qty}, AvgPrice={avg_price}"
            )

            return OrderResult(
                success=True,
                order_id=order_id,
                symbol=order_input.symbol,
                status=status,
                executed_qty=executed_qty,
                avg_price=float(avg_price) if avg_price else None,
                message="Order placed successfully",
                raw_response=response,
            )

        except BinanceAPIError as e:
            error_msg = self._format_api_error(e)
            logger.error(f"API error placing order: {error_msg}")
            return OrderResult(
                success=False,
                symbol=order_input.symbol,
                message=error_msg,
                raw_response=e.response,
            )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error placing order: {e}")
            return OrderResult(
                success=False,
                symbol=order_input.symbol,
                message=error_msg,
            )

    def _format_api_error(self, error: BinanceAPIError) -> str:
        """Format API error for user-friendly display.

        Args:
            error: BinanceAPIError instance.

        Returns:
            Formatted error message.
        """
        # Common error code mappings
        error_messages = {
            -2010: "Insufficient balance for this order.",
            -1100: "Invalid character in request parameter.",
            -1101: "Too many parameters in request.",
            -1102: "Missing required parameter.",
            -1103: "Unknown parameter in request.",
            -1104: "Duplicate parameter in request.",
            -1105: "Empty parameter value.",
            -2011: "Unknown order sent.",
            -2012: "Order is already cancelled.",
            -2013: "Order does not exist.",
            -2014: "API key format invalid.",
            -2015: "Invalid API key, IP, or permission.",
            -2026: "Order cost exceeds account balance.",
            -4000: "Invalid price or quantity precision.",
            -4001: "Price is not within valid range.",
            -4002: "Quantity is below minimum.",
            -4003: "Quantity exceeds maximum.",
            -4004: "Invalid order type.",
            -4005: "Invalid side parameter.",
            -4014: "Price is too high or too low.",
            -4015: "Stop price is too high or too low.",
            -4046: "No need to change leverage (already set).",
            -4061: "Order type requires stop price.",
            -4062: "Stop price invalid.",
        }

        code = error.code
        msg = error.message

        # Check for known error codes
        if code in error_messages:
            return f"{error_messages[code]} (Code: {code})"

        # Return original message if not known
        return f"{msg} (Code: {code})" if code else msg

    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get the status of an order.

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID.

        Returns:
            Order status information.
        """
        try:
            response = self.client.get_order(symbol=symbol, order_id=order_id)
            logger.info(f"Retrieved order status for {order_id}")
            return response
        except BinanceAPIError as e:
            logger.error(f"Failed to get order status: {e}")
            return {"error": str(e)}

    def cancel_order(self, symbol: str, order_id: int) -> OrderResult:
        """Cancel an existing order.

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID to cancel.

        Returns:
            OrderResult with cancellation details.
        """
        logger.info(f"Cancelling order {order_id} for {symbol}")

        try:
            response = self.client.cancel_order(
                symbol=symbol, order_id=order_id
            )

            return OrderResult(
                success=True,
                order_id=response.get("orderId"),
                symbol=response.get("symbol"),
                status=response.get("status"),
                message="Order cancelled successfully",
                raw_response=response,
            )

        except BinanceAPIError as e:
            error_msg = self._format_api_error(e)
            logger.error(f"Failed to cancel order: {error_msg}")
            return OrderResult(
                success=False,
                symbol=symbol,
                message=error_msg,
            )

    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get all open orders.

        Args:
            symbol: Optional symbol to filter results.

        Returns:
            List of open orders or error information.
        """
        try:
            response = self.client.get_open_orders(symbol=symbol)
            logger.info(f"Retrieved {len(response)} open orders")
            return {"success": True, "orders": response}
        except BinanceAPIError as e:
            logger.error(f"Failed to get open orders: {e}")
            return {"success": False, "error": str(e)}

    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol.

        Args:
            symbol: Trading pair symbol.
            leverage: Leverage value (1-125).

        Returns:
            Response with leverage information.
        """
        logger.info(f"Setting leverage for {symbol} to {leverage}x")

        try:
            response = self.client.set_leverage(
                symbol=symbol, leverage=leverage
            )
            logger.info(f"Leverage set successfully: {response}")
            return {"success": True, "response": response}
        except BinanceAPIError as e:
            # Handle "no change needed" as success
            if e.code == -4046:
                logger.info(f"Leverage already set to {leverage}x")
                return {
                    "success": True,
                    "message": f"Leverage already set to {leverage}x",
                }

            logger.error(f"Failed to set leverage: {e}")
            return {"success": False, "error": str(e)}

    def get_account_balance(self, asset: str = "USDT") -> Dict[str, Any]:
        """Get account balance for an asset.

        Args:
            asset: Asset symbol (default: USDT).

        Returns:
            Balance information.
        """
        try:
            balance = self.client.get_balance(asset=asset)
            logger.info(f"Retrieved balance for {asset}")
            return {
                "success": True,
                "asset": balance.get("asset"),
                "available": float(balance.get("availableBalance", 0)),
                "total": float(balance.get("totalBalance", 0)),
            }
        except BinanceAPIError as e:
            logger.error(f"Failed to get balance: {e}")
            return {"success": False, "error": str(e)}
