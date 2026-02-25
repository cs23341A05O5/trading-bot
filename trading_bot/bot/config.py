"""Configuration management for the trading bot.

Handles loading API credentials from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration settings for Binance Futures API.

    Attributes:
        api_key: Binance API key for authentication.
        api_secret: Binance API secret for signing requests.
        base_url: Base URL for Binance Futures Testnet API.
        default_leverage: Default leverage for futures trading.
    """

    api_key: str
    api_secret: str
    base_url: str = "https://testnet.binancefuture.com"
    default_leverage: int = 1


def load_config(env_path: Optional[str] = None) -> Config:
    """Load configuration from environment variables.

    Args:
        env_path: Optional path to .env file. If None, uses default .env lookup.

    Returns:
        Config object with loaded settings.

    Raises:
        ValueError: If API_KEY or API_SECRET is not set in environment.
    """
    # Load .env file if it exists
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    base_url = os.getenv("BASE_URL", "https://testnet.binancefuture.com")
    default_leverage = int(os.getenv("DEFAULT_LEVERAGE", "1"))

    if not api_key:
        raise ValueError(
            "API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )

    if not api_secret:
        raise ValueError(
            "API_SECRET not found in environment variables. "
            "Please set it in your .env file."
        )

    return Config(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
        default_leverage=default_leverage,
    )
