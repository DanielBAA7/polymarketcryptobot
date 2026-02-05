# Polymarket Transaction Listener

A Python CLI application that continuously monitors a Polymarket user's transactions using the Data API.

## Features

- 🔄 **Real-time monitoring** - Polls for new transactions at configurable intervals
- 🎨 **Colored logging** - Clear visual distinction between log types
- 🏗️ **Clean architecture** - Modular design with separation of concerns
- ⚡ **Error resilient** - Automatic retry logic with exponential backoff

## Installation

1. Clone the repository:
   ```bash
   cd c:\Users\danie\Documents\git-projects
   git clone <repo-url> polymarket-listener
   cd polymarket-listener
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Copy and configure environment variables:
   ```bash
   copy .env.example .env
   ```

## Usage

### Basic Usage

```bash
python main.py --user <POLYMARKET_WALLET_ADDRESS>
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--user` | Polymarket wallet address (required) | - |
| `--interval` | Polling interval in seconds | 30 |
| `--limit` | Max transactions per request | 100 |
| `--debug` | Enable debug logging | False |

### Examples

```bash
# Monitor a user with default settings
python main.py --user 0x1234567890abcdef1234567890abcdef12345678

# Custom polling interval (every 10 seconds)
python main.py --user 0x... --interval 10

# Enable debug logging
python main.py --user 0x... --debug
```

## Project Structure

```
polymarketcryptobot/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── README.md                  # Documentation
├── .env.example              # Environment template
└── src/
    ├── config/settings.py     # Configuration management
    ├── api/polymarket_client.py  # API client
    ├── models/transaction.py  # Data models
    ├── services/listener.py   # Transaction listener
    └── logging/logger.py      # Colored logging
```

## Log Color Codes

| Level | Color | Description |
|-------|-------|-------------|
| DEBUG | Gray | Verbose details |
| INFO | Cyan | General information |
| SUCCESS | Green | New transactions found |
| WARNING | Yellow | Retries, rate limits |
| ERROR | Red | API failures |

## API Reference

This application uses the [Polymarket Data API](https://docs.polymarket.com):
- **Base URL**: `https://data-api.polymarket.com`
- **Endpoint**: `GET /activity?user={address}`

## License

MIT
