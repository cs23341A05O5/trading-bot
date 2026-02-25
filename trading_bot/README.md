# 🤖 Binance Futures Trading Bot

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A production-quality CLI trading bot for Binance Futures Testnet**

</div>

---

## 📋 Overview

A **production-ready**, **interview-quality** Python trading bot that interfaces with the **Binance Futures Testnet (USDT-M)**. Built with clean architecture, comprehensive error handling, and professional logging.

### ✨ Key Highlights

- 🎯 **Clean Architecture**: Modular design with separation of concerns
- 🔒 **Secure**: API keys via environment variables, never committed to git
- 📝 **Well-Documented**: Full docstrings, type hints, and comprehensive README
- ✅ **Tested**: Unit tests with pytest for validation logic
- 🎨 **Beautiful CLI**: Colored output with Rich library
- 🔄 **Retry Logic**: Automatic retry for failed API requests
- 📊 **Professional Logging**: Rotating logs with timestamps

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **Order Types** | MARKET, LIMIT, STOP-LIMIT orders |
| **Order Sides** | BUY and SELL support |
| **Interactive Mode** | User-friendly menu-driven interface |
| **Position Tracking** | View active positions with PnL |
| **Order History** | View past orders with status |
| **Balance Check** | Check USDT and other asset balances |
| **Leverage Control** | Set leverage per symbol |
| **Input Validation** | Comprehensive CLI argument validation |
| **Error Handling** | Friendly error messages with full logging |
| **Colored Output** | Rich-formatted tables and panels |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer (cli.py)                        │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │  place  │ │  cancel  │ │  orders  │ │ position │ │ history │ │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ │
└───────┼───────────┼────────────┼────────────┼────────────┼──────┘
        │           │            │            │            │
        ▼           ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic (bot/)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  validators  │  │   orders     │  │  logging_config      │  │
│  │  (Pydantic)  │  │  (manager)   │  │  (rotation)          │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    client.py                               │  │
│  │  • HMAC SHA256 Authentication                             │  │
│  │  • Retry Mechanism (3 retries, backoff)                   │  │
│  │  • Request/Response Logging                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Binance Futures Testnet API                      │
│  Base URL: https://testnet.binancefuture.com                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
trading_bot/
│
├── bot/                        # Core business logic
│   ├── __init__.py            # Package initialization
│   ├── client.py              # Binance API wrapper (auth, retry)
│   ├── config.py              # Environment configuration
│   ├── logging_config.py      # Logging setup with rotation
│   ├── orders.py              # Order management logic
│   └── validators.py          # Input validation (Pydantic)
│
├── tests/                      # Unit tests
│   ├── __init__.py
│   └── test_validators.py     # Validator tests
│
├── cli.py                      # Main CLI interface
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── CHECKLIST.md               # GitHub readiness checklist
└── logs/                      # Log files (auto-created)
    └── trading_bot.log
```

## Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Step 1: Clone/Download the Project

```bash
cd trading_bot
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create Binance Testnet Account

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Click "Register" or "Sign Up"
3. Create a testnet account (this is separate from your main Binance account)
4. Log in to the testnet dashboard

### Step 5: Generate API Keys

1. In the testnet dashboard, go to **API Management**
2. Click **Create API**
3. Give your API key a label (e.g., "Trading Bot")
4. Copy both the **API Key** and **Secret Key**
5. **Important**: Store these securely - you won't be able to see the secret again

### Step 6: Configure Environment Variables

```bash
# Copy the example file
copy .env.example .env    # Windows
# cp .env.example .env   # Linux/macOS
```

Edit `.env` and add your credentials:

```env
API_KEY=your_actual_api_key_here
API_SECRET=your_actual_api_secret_here
BASE_URL=https://testnet.binancefuture.com
DEFAULT_LEVERAGE=1
```

### Step 7: Test Connection

```bash
python cli.py test
```

You should see:
```
✓ API connection successful!
USDT Balance: 10000.00000000
```

## Usage

### Place a Market Order

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a Limit Order

```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000
```

### Place a Stop-Limit Order

```bash
python cli.py place --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --price 60000 --stop-price 61000
```

### Set Leverage

```bash
python cli.py leverage BTCUSDT 10
```

### View Open Orders

```bash
# All open orders
python cli.py orders

# Filter by symbol
python cli.py orders --symbol BTCUSDT
```

### Cancel an Order

```bash
python cli.py cancel --symbol BTCUSDT --order-id 12345
```

### Check Balance

```bash
python cli.py balance --asset USDT
```

### Interactive Mode

Launch the interactive menu:

```bash
python cli.py interactive
```

This provides a user-friendly menu for all operations:

```
╭──────────────────────────────────────╮
│ Binance Futures Trading Bot          │
│ Interactive Mode                     │
╰──────────────────────────────────────╯

Main Menu:
  1. Place Market Order
  2. Place Limit Order
  3. Place Stop-Limit Order
  4. View Open Orders
  5. Check Balance
  6. Set Leverage
  7. Cancel Order
  8. Test Connection
  0. Exit
```

## Sample CLI Output

### Successful Market Order

```
        Order Summary        
┌─────────┬──────────┐
│ Symbol  │ BTCUSDT  │
│ Side    │ BUY      │
│ Type    │ MARKET   │
│ Qty     │ 0.001    │
└─────────┴──────────┘

Proceed with order placement? [y/N]: y

╭──────────────────────────╮
│   ✓ ORDER SUCCESS        │
╰──────────────────────────╯

    Response    
┌─────────────┬──────────┐
│ OrderID     │ 12345    │
│ Symbol      │ BTCUSDT  │
│ Status      │ FILLED   │
│ ExecutedQty │ 0.001    │
│ AvgPrice    │ 61000.00 │
└─────────────┴──────────┘
```

### Failed Order (Insufficient Balance)

```
╭──────────────────────────────────────────────╮
│ Error                                        │
├──────────────────────────────────────────────┤
│ ✗ ORDER FAILED                               │
│                                              │
│ Insufficient balance for this order.         │
│ (Code: -2010)                                │
╰──────────────────────────────────────────────╯
```

## CLI Commands Reference

| Command | Description | Required Arguments |
|---------|-------------|-------------------|
| `place` | Place a new order | `--symbol`, `--side`, `--type`, `--quantity` |
| `cancel` | Cancel an existing order | `--symbol`, `--order-id` |
| `orders` | List open orders | Optional: `--symbol` |
| `history` | View order history | Optional: `--symbol`, `--limit` |
| `position` | View active positions | Optional: `--symbol` |
| `balance` | Check account balance | Optional: `--asset` (default: USDT) |
| `leverage` | Set leverage for symbol | `--symbol`, leverage value |
| `test` | Test API connection | None |
| `interactive` | Launch interactive menu | None |

### Place Command Options

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--symbol` | `-s` | Trading pair (e.g., BTCUSDT) | Yes |
| `--side` | | BUY or SELL | Yes |
| `--type` | `-t` | MARKET, LIMIT, or STOP_LIMIT | Yes |
| `--quantity` | `-q` | Order quantity | Yes |
| `--price` | `-p` | Limit price | For LIMIT/STOP_LIMIT |
| `--stop-price` | | Stop price | For STOP_LIMIT |
| `--leverage` | `-l` | Set leverage before order | No |
| `--no-confirm` | | Skip confirmation prompt | No |

## Logging

All operations are logged to `logs/trading_bot.log` with:

- **Timestamp**: When the event occurred
- **Log Level**: INFO, WARNING, ERROR, etc.
- **Module**: Which module generated the log
- **Message**: Detailed log message

Log rotation is configured:
- **Max file size**: 5 MB
- **Backup count**: 5 files

Example log entry:
```
2024-01-15 14:30:25 | INFO     | client:_make_request:85 | Making POST request to /fapi/v1/order
2024-01-15 14:30:26 | INFO     | orders:place_order:45 | Order placed successfully: ID=12345, Status=FILLED
```

## Assumptions

1. **Testnet Only**: This bot is designed for Binance Futures Testnet, not production/mainnet.
2. **USDT-M Futures**: Only USDT-margined futures are supported.
3. **Python 3.10+**: Uses modern Python features like type hints and pattern matching.
4. **Single User**: The bot is designed for single-user operation.
5. **Manual Order Placement**: Orders are placed manually via CLI, not automated trading strategies.

## Troubleshooting

### "API_KEY not found in environment variables"

**Cause**: The `.env` file is missing or not configured.

**Solution**: 
1. Ensure `.env` file exists in the project root
2. Verify the file contains `API_KEY=your_key`
3. Check the file is named `.env` (not `.env.txt`)

### "Invalid API key, IP, or permission"

**Cause**: API credentials are incorrect or not properly set up.

**Solution**:
1. Verify API key and secret are correct
2. Ensure you're using Testnet API keys (not mainnet)
3. Regenerate API keys if necessary

### "Insufficient balance for this order"

**Cause**: Not enough USDT in your testnet account.

**Solution**:
1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Navigate to "Wallet" → "Get Test Funds"
3. Request more test USDT

### "Connection error" / "Request timed out"

**Cause**: Network connectivity issues.

**Solution**:
1. Check your internet connection
2. Verify Binance Testnet is accessible
3. Try again after a few seconds

### "Price is not within valid range"

**Cause**: Limit price is too far from current market price.

**Solution**:
1. Check current market price on Binance
2. Adjust your limit price to be within reasonable range

### "Quantity is below minimum"

**Cause**: Order quantity is below the minimum for the symbol.

**Solution**:
1. Check minimum order size for the symbol
2. Increase quantity to meet minimum requirements

### Module Import Errors

**Cause**: Dependencies not installed or virtual environment not activated.

**Solution**:
```bash
# Activate virtual environment
venv\Scripts\activate     # Windows
source venv/bin/activate  # Linux/macOS

# Reinstall dependencies
pip install -r requirements.txt
```

## Development

### Running Tests

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=bot
```

### Code Quality

```bash
pip install pylint black mypy
pylint bot/
black bot/
mypy bot/
```

## Security Notes

1. **Never commit `.env` file** to version control
2. **Use testnet credentials only** - never use mainnet keys
3. **Rotate API keys** periodically
4. **Restrict API permissions** to only what's needed (trading only)

## License

MIT License - Use at your own risk. This is for educational and testing purposes only.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the logs in `logs/trading_bot.log`
3. Open an issue with full error details and logs
