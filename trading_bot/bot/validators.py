"""Input validation for trading bot CLI.

Provides validation functions for CLI arguments.
"""

import re
from enum import Enum
from typing import Optional, Tuple

from pydantic import BaseModel, field_validator, model_validator


class OrderSide(str, Enum):
    """Order side enumeration."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


class OrderInput(BaseModel):
    """Validated order input model.

    Attributes:
        symbol: Trading pair symbol (e.g., BTCUSDT).
        side: Order side (BUY or SELL).
        order_type: Order type (MARKET, LIMIT, STOP_LIMIT).
        quantity: Order quantity.
        price: Limit price (required for LIMIT and STOP_LIMIT orders).
        stop_price: Stop price (required for STOP_LIMIT orders).
    """

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate trading pair symbol format.

        Args:
            v: Symbol string to validate.

        Returns:
            Uppercase symbol string.

        Raises:
            ValueError: If symbol format is invalid.
        """
        if not v:
            raise ValueError("Symbol cannot be empty")

        # Convert to uppercase
        v = v.upper().strip()

        # Validate format: should be alphanumeric and typically ends with USDT
        if not re.match(r"^[A-Z0-9]{3,20}$", v):
            raise ValueError(
                f"Invalid symbol format: '{v}'. "
                "Symbol should be 3-20 uppercase alphanumeric characters "
                "(e.g., BTCUSDT, ETHUSDT)."
            )

        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        """Validate order quantity.

        Args:
            v: Quantity to validate.

        Returns:
            Validated quantity.

        Raises:
            ValueError: If quantity is invalid.
        """
        if v <= 0:
            raise ValueError(f"Quantity must be positive, got: {v}")

        # Check for reasonable precision (max 6 decimal places)
        if round(v, 6) != v:
            raise ValueError(
                f"Quantity has too many decimal places: {v}. "
                "Maximum 6 decimal places allowed."
            )

        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        """Validate limit price.

        Args:
            v: Price to validate.

        Returns:
            Validated price.

        Raises:
            ValueError: If price is invalid.
        """
        if v is not None:
            if v <= 0:
                raise ValueError(f"Price must be positive, got: {v}")

            # Check for reasonable precision (max 8 decimal places)
            if round(v, 8) != v:
                raise ValueError(
                    f"Price has too many decimal places: {v}. "
                    "Maximum 8 decimal places allowed."
                )

        return v

    @field_validator("stop_price")
    @classmethod
    def validate_stop_price(cls, v: Optional[float]) -> Optional[float]:
        """Validate stop price.

        Args:
            v: Stop price to validate.

        Returns:
            Validated stop price.

        Raises:
            ValueError: If stop price is invalid.
        """
        if v is not None:
            if v <= 0:
                raise ValueError(f"Stop price must be positive, got: {v}")

        return v

    @model_validator(mode="after")
    def validate_order_requirements(self) -> "OrderInput":
        """Validate that required fields are present based on order type.

        Returns:
            Validated OrderInput.

        Raises:
            ValueError: If required fields are missing.
        """
        # LIMIT orders require price
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError(
                "LIMIT orders require a price. "
                "Please provide --price argument."
            )

        # STOP_LIMIT orders require both price and stop_price
        if self.order_type == OrderType.STOP_LIMIT:
            if self.price is None:
                raise ValueError(
                    "STOP_LIMIT orders require a limit price. "
                    "Please provide --price argument."
                )
            if self.stop_price is None:
                raise ValueError(
                    "STOP_LIMIT orders require a stop price. "
                    "Please provide --stop-price argument."
                )

        return self


def validate_cli_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Tuple[OrderInput, str]:
    """Validate CLI input and return parsed values.

    Args:
        symbol: Trading pair symbol.
        side: Order side (BUY/SELL).
        order_type: Order type (MARKET/LIMIT/STOP_LIMIT).
        quantity: Order quantity.
        price: Limit price (optional).
        stop_price: Stop price (optional).

    Returns:
        Tuple of (OrderInput model, error message if any).

    Note:
        If validation fails, OrderInput will be None and error message will be set.
    """
    try:
        # Parse side
        try:
            parsed_side = OrderSide(side.upper())
        except ValueError:
            valid_sides = [s.value for s in OrderSide]
            return None, (
                f"Invalid side: '{side}'. "
                f"Valid options are: {', '.join(valid_sides)}"
            )

        # Parse order type
        try:
            parsed_type = OrderType(order_type.upper())
        except ValueError:
            valid_types = [t.value for t in OrderType]
            return None, (
                f"Invalid order type: '{order_type}'. "
                f"Valid options are: {', '.join(valid_types)}"
            )

        # Create and validate OrderInput
        order_input = OrderInput(
            symbol=symbol,
            side=parsed_side,
            order_type=parsed_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        return order_input, ""

    except ValueError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Unexpected validation error: {e}"
