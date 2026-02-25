"""Unit tests for the validators module.

Tests cover all validation functions and edge cases.
"""

import pytest
from pydantic import ValidationError

from bot.validators import (
    OrderInput,
    OrderSide,
    OrderType,
    validate_cli_input,
)


class TestOrderSide:
    """Tests for OrderSide enum."""

    def test_valid_buy_side(self) -> None:
        """Test BUY side is valid."""
        assert OrderSide.BUY.value == "BUY"

    def test_valid_sell_side(self) -> None:
        """Test SELL side is valid."""
        assert OrderSide.SELL.value == "SELL"

    def test_case_insensitive(self) -> None:
        """Test side parsing is case insensitive."""
        assert OrderSide("buy") == OrderSide.BUY
        assert OrderSide("SELL") == OrderSide.SELL


class TestOrderType:
    """Tests for OrderType enum."""

    def test_valid_market_type(self) -> None:
        """Test MARKET type is valid."""
        assert OrderType.MARKET.value == "MARKET"

    def test_valid_limit_type(self) -> None:
        """Test LIMIT type is valid."""
        assert OrderType.LIMIT.value == "LIMIT"

    def test_valid_stop_limit_type(self) -> None:
        """Test STOP_LIMIT type is valid."""
        assert OrderType.STOP_LIMIT.value == "STOP_LIMIT"


class TestOrderInput:
    """Tests for OrderInput validation."""

    def test_valid_market_order(self) -> None:
        """Test valid market order input."""
        order = OrderInput(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.001,
        )
        assert order.symbol == "BTCUSDT"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 0.001

    def test_valid_limit_order(self) -> None:
        """Test valid limit order input."""
        order = OrderInput(
            symbol="ETHUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=0.1,
            price=2500.00,
        )
        assert order.price == 2500.00

    def test_valid_stop_limit_order(self) -> None:
        """Test valid stop-limit order input."""
        order = OrderInput(
            symbol="BTCUSDT",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=0.001,
            price=60000.00,
            stop_price=61000.00,
        )
        assert order.price == 60000.00
        assert order.stop_price == 61000.00

    def test_symbol_uppercase_conversion(self) -> None:
        """Test symbol is converted to uppercase."""
        order = OrderInput(
            symbol="btcusdt",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.001,
        )
        assert order.symbol == "BTCUSDT"

    def test_symbol_whitespace_stripped(self) -> None:
        """Test symbol whitespace is stripped."""
        order = OrderInput(
            symbol="  BTCUSDT  ",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.001,
        )
        assert order.symbol == "BTCUSDT"

    def test_invalid_symbol_empty(self) -> None:
        """Test empty symbol raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.001,
            )

    def test_invalid_symbol_format(self) -> None:
        """Test invalid symbol format raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTC-USDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.001,
            )

    def test_invalid_symbol_too_short(self) -> None:
        """Test symbol too short raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="AB",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.001,
            )

    def test_invalid_quantity_zero(self) -> None:
        """Test zero quantity raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0,
            )

    def test_invalid_quantity_negative(self) -> None:
        """Test negative quantity raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=-0.001,
            )

    def test_quantity_precision_valid(self) -> None:
        """Test quantity with 6 decimal places is valid."""
        order = OrderInput(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.123456,
        )
        assert order.quantity == 0.123456

    def test_quantity_precision_invalid(self) -> None:
        """Test quantity with too many decimals raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.1234567,
            )

    def test_invalid_price_zero(self) -> None:
        """Test zero price raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.001,
                price=0,
            )

    def test_invalid_price_negative(self) -> None:
        """Test negative price raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.001,
                price=-100,
            )

    def test_limit_order_requires_price(self) -> None:
        """Test LIMIT order without price raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=0.001,
            )

    def test_stop_limit_requires_price(self) -> None:
        """Test STOP_LIMIT order without price raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.STOP_LIMIT,
                quantity=0.001,
                stop_price=60000,
            )

    def test_stop_limit_requires_stop_price(self) -> None:
        """Test STOP_LIMIT order without stop price raises error."""
        with pytest.raises(ValidationError):
            OrderInput(
                symbol="BTCUSDT",
                side=OrderSide.SELL,
                order_type=OrderType.STOP_LIMIT,
                quantity=0.001,
                price=60000,
            )


class TestValidateCliInput:
    """Tests for validate_cli_input function."""

    def test_valid_market_order_input(self) -> None:
        """Test valid market order CLI input."""
        order, error = validate_cli_input(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0.001,
        )
        assert error == ""
        assert order is not None
        assert order.symbol == "BTCUSDT"

    def test_valid_limit_order_input(self) -> None:
        """Test valid limit order CLI input."""
        order, error = validate_cli_input(
            symbol="BTCUSDT",
            side="SELL",
            order_type="LIMIT",
            quantity=0.001,
            price=65000,
        )
        assert error == ""
        assert order is not None
        assert order.price == 65000

    def test_invalid_side(self) -> None:
        """Test invalid side returns error."""
        order, error = validate_cli_input(
            symbol="BTCUSDT",
            side="HOLD",
            order_type="MARKET",
            quantity=0.001,
        )
        assert order is None
        assert "Invalid side" in error

    def test_invalid_order_type(self) -> None:
        """Test invalid order type returns error."""
        order, error = validate_cli_input(
            symbol="BTCUSDT",
            side="BUY",
            order_type="IOC",
            quantity=0.001,
        )
        assert order is None
        assert "Invalid order type" in error

    def test_case_insensitive_side(self) -> None:
        """Test side parsing is case insensitive."""
        order, error = validate_cli_input(
            symbol="BTCUSDT",
            side="buy",
            order_type="MARKET",
            quantity=0.001,
        )
        assert error == ""
        assert order.side == OrderSide.BUY

    def test_case_insensitive_order_type(self) -> None:
        """Test order type parsing is case insensitive."""
        order, error = validate_cli_input(
            symbol="BTCUSDT",
            side="BUY",
            order_type="market",
            quantity=0.001,
        )
        assert error == ""
        assert order.order_type == OrderType.MARKET

    def test_missing_price_for_limit(self) -> None:
        """Test missing price for LIMIT order returns error."""
        order, error = validate_cli_input(
            symbol="BTCUSDT",
            side="BUY",
            order_type="LIMIT",
            quantity=0.001,
        )
        assert order is None
        assert "price" in error.lower()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_quantity(self) -> None:
        """Test very small quantity is valid."""
        order = OrderInput(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.000001,
        )
        assert order.quantity == 0.000001

    def test_very_large_quantity(self) -> None:
        """Test large quantity is valid."""
        order = OrderInput(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000000.0,
        )
        assert order.quantity == 1000000.0

    def test_very_small_price(self) -> None:
        """Test very small price is valid."""
        order = OrderInput(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.001,
            price=0.00000001,
        )
        assert order.price == 0.00000001

    def test_very_large_price(self) -> None:
        """Test large price is valid."""
        order = OrderInput(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=0.001,
            price=1000000.0,
        )
        assert order.price == 1000000.0

    def test_symbol_exactly_3_chars(self) -> None:
        """Test symbol with exactly 3 characters is valid."""
        order = OrderInput(
            symbol="BTC",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.001,
        )
        assert order.symbol == "BTC"

    def test_symbol_exactly_20_chars(self) -> None:
        """Test symbol with exactly 20 characters is valid."""
        order = OrderInput(
            symbol="A" * 20,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=0.001,
        )
        assert order.symbol == "A" * 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
