"""Binance Futures API client wrapper.

Provides a clean interface for interacting with Binance Futures Testnet API.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.config import Config
from bot.logging_config import get_logger

logger = get_logger("client")


class BinanceAPIError(Exception):
    """Exception raised for Binance API errors.

    Attributes:
        code: Error code from Binance API.
        message: Error message from Binance API.
        response: Full API response that caused the error.
    """

    def __init__(
        self,
        message: str,
        code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        """Initialize BinanceAPIError.

        Args:
            message: Error message.
            code: Optional error code from Binance.
            response: Optional full API response.
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.response = response or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.code:
            return f"Binance API Error [{self.code}]: {self.message}"
        return f"Binance API Error: {self.message}"


class BinanceClient:
    """Binance Futures API client.

    Provides methods for authentication and API calls to Binance Futures Testnet.

    Attributes:
        config: Configuration object with API credentials.
        session: Requests session with retry mechanism.
    """

    def __init__(self, config: Config, timeout: int = 30):
        """Initialize Binance client.

        Args:
            config: Configuration object with API credentials.
            timeout: Request timeout in seconds.
        """
        self.config = config
        self.timeout = timeout
        self.session = self._create_session()
        logger.info(
            f"BinanceClient initialized with base URL: {config.base_url}"
        )

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry mechanism.

        Returns:
            Configured requests session with retry strategy.
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for API request.

        Args:
            params: Request parameters to sign.

        Returns:
            Hexadecimal signature string.
        """
        query_string = "&".join(
            f"{key}={value}" for key, value in sorted(params.items())
        )
        signature = hmac.new(
            self.config.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        logger.debug(f"Generated signature for params: {params}")
        return signature

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = True,
    ) -> Dict[str, Any]:
        """Make an HTTP request to Binance API.

        Args:
            method: HTTP method (GET, POST, DELETE).
            endpoint: API endpoint path.
            params: Request parameters.
            signed: Whether the request requires authentication.

        Returns:
            API response as dictionary.

        Raises:
            BinanceAPIError: If API returns an error.
            requests.RequestException: If network request fails.
        """
        url = f"{self.config.base_url}{endpoint}"
        params = params or {}

        # Add timestamp for signed requests
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            params["signature"] = self._generate_signature(params)

        headers = {
            "X-MBX-APIKEY": self.config.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        logger.info(f"Making {method} request to {endpoint}")
        logger.debug(f"Request params: {params}")

        try:
            if method == "GET":
                response = self.session.get(
                    url, params=params, headers=headers, timeout=self.timeout
                )
            elif method == "POST":
                response = self.session.post(
                    url, params=params, headers=headers, timeout=self.timeout
                )
            elif method == "DELETE":
                response = self.session.delete(
                    url, params=params, headers=headers, timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text[:500]}")

            # Parse response
            data = response.json()

            # Check for API errors
            if response.status_code != 200:
                error_code = data.get("code", response.status_code)
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"API error: {error_code} - {error_msg}")
                raise BinanceAPIError(
                    message=error_msg,
                    code=error_code,
                    response=data,
                )

            logger.info(f"Successful response from {endpoint}")
            return data

        except requests.Timeout:
            logger.error(f"Request timeout for {endpoint}")
            raise BinanceAPIError(
                message="Request timed out. Please check your network connection."
            )
        except requests.ConnectionError:
            logger.error(f"Connection error for {endpoint}")
            raise BinanceAPIError(
                message="Failed to connect to Binance API. Please check your network."
            )
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            raise BinanceAPIError(message=f"Network error: {str(e)}")

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get exchange information.

        Args:
            symbol: Optional symbol to filter results.

        Returns:
            Exchange information dictionary.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()

        return self._make_request("GET", "/fapi/v1/exchangeInfo", params, signed=False)

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information.

        Returns:
            Account information dictionary.
        """
        return self._make_request("GET", "/fapi/v2/account", signed=True)

    def get_balance(self, asset: str = "USDT") -> Dict[str, Any]:
        """Get balance for a specific asset.

        Args:
            asset: Asset symbol (default: USDT).

        Returns:
            Balance information dictionary.
        """
        account = self.get_account_info()
        for balance in account.get("assets", []):
            if balance.get("asset") == asset:
                return balance

        return {"asset": asset, "availableBalance": "0", "totalBalance": "0"}

    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol.

        Args:
            symbol: Trading pair symbol.
            leverage: Leverage value (1-125).

        Returns:
            API response with leverage information.
        """
        params = {"symbol": symbol.upper(), "leverage": leverage}
        return self._make_request("POST", "/fapi/v1/leverage", params, signed=True)

    def get_position_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get position information.

        Args:
            symbol: Optional symbol to filter results.

        Returns:
            Position information.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()

        return self._make_request("GET", "/fapi/v2/positionRisk", params, signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """Place a futures order.

        Args:
            symbol: Trading pair symbol.
            side: Order side (BUY or SELL).
            order_type: Order type (MARKET, LIMIT, STOP).
            quantity: Order quantity.
            price: Limit price (required for LIMIT orders).
            stop_price: Stop price (required for STOP orders).
            time_in_force: Time in force (GTC, IOC, FOK).
            reduce_only: Whether this is a reduce-only order.

        Returns:
            Order response dictionary.

        Raises:
            BinanceAPIError: If order placement fails.
        """
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
        }

        if reduce_only:
            params["reduceOnly"] = "true"

        # MARKET orders don't need timeInForce
        if order_type.upper() not in ["MARKET"]:
            params["timeInForce"] = time_in_force

        # Add price for LIMIT and STOP orders
        if order_type.upper() in ["LIMIT", "STOP"]:
            if price is None:
                raise BinanceAPIError(
                    message=f"Price is required for {order_type} orders"
                )
            params["price"] = price

        # Add stop price for STOP orders
        if order_type.upper() == "STOP":
            if stop_price is None:
                raise BinanceAPIError(
                    message="Stop price is required for STOP orders"
                )
            params["stopPrice"] = stop_price

        logger.info(
            f"Placing {order_type} {side} order: {quantity} {symbol} "
            f"@ {price if price else 'market'}"
        )

        return self._make_request("POST", "/fapi/v1/order", params, signed=True)

    def cancel_order(
        self, symbol: str, order_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Cancel an order.

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID to cancel.

        Returns:
            Cancellation response.
        """
        params = {"symbol": symbol.upper()}

        if order_id:
            params["orderId"] = order_id
        else:
            raise BinanceAPIError(message="Order ID is required")

        return self._make_request("DELETE", "/fapi/v1/order", params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order information.

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID.

        Returns:
            Order information dictionary.
        """
        params = {"symbol": symbol.upper(), "orderId": order_id}
        return self._make_request("GET", "/fapi/v1/order", params, signed=True)

    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get all open orders.

        Args:
            symbol: Optional symbol to filter results.

        Returns:
            List of open orders.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()

        return self._make_request("GET", "/fapi/v1/openOrders", params, signed=True)

    def test_connection(self) -> bool:
        """Test API connection and authentication.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            # Test public endpoint
            self.get_exchange_info()
            logger.info("Public API connection successful")

            # Test private endpoint
            self.get_account_info()
            logger.info("Private API connection successful")

            return True
        except BinanceAPIError as e:
            logger.error(f"Connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False
