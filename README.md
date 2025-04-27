# Algorithmic Trading Bot

An automated trading bot for Binance that uses technical analysis indicators to make trading decisions. The bot implements multiple trading strategies and includes risk management features.

## Features

- **Multiple Trading Strategies**:
  - Bollinger Band Squeeze
  - RSI + MACD Combination
  - ADX Trend Strength Analysis

- **Risk Management**:
  - Daily trade limits
  - Stop-loss and take-profit levels
  - Position sizing based on account balance

- **Real-time Monitoring**:
  - Color-coded trading signals
  - Market condition indicators
  - Trade execution status

- **Technical Indicators**:
  - Bollinger Bands
  - Keltner Channels
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - ADX (Average Directional Index)

## Color-Coded Signals

The bot uses color-coded signals for better visibility:

- **Buy Signals** (Green):
  - `[BUY]` - Indicates a buy signal
  - `[SUCCESS]` - Trade executed successfully

- **Sell Signals** (Red):
  - `[SELL]` - Indicates a sell signal
  - `[FAILED]` - Trade execution failed

- **Hold/Pending Signals** (Yellow):
  - `[HOLD]` - No clear trading signal
  - `[PENDING]` - Trade in progress

- **Market Conditions**:
  - RSI: Green (<30), Red (>70), Yellow (in between)
  - MACD: Green (bullish), Red (bearish)
  - ADX: Green (strong trend), Yellow (weak trend)
  - Price: Cyan for better visibility

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/algorithmic-trading-bot.git
cd algorithmic-trading-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
cp .env_example .env
```

4. Edit the `.env` file with your Binance API credentials and trading parameters.

## Configuration

The bot can be configured through environment variables in the `.env` file:

### Required Variables
```
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
TRADING_SYMBOL=BTCUSDT
TRADING_INTERVAL=1h
TRADING_QUANTITY=0.001
MAX_TRADES_PER_DAY=5
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=3.0
```

### Optional Variables (with defaults)
```
BB_WINDOW=20
BB_STD=2.0
KELTNER_WINDOW=20
KELTNER_ATR_MULT=1.5
ADX_PERIOD=14
ADX_THRESHOLD=25
RSI_PERIOD=14
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
```

## Usage

1. Start the trading bot:
```bash
python binance_trader.py
```

2. Monitor the output:
- The bot will display color-coded signals and market conditions
- Trades will be logged to `trades.csv`
- General logs will be saved to `trading_bot.log`

## Trading Strategies

### 1. Bollinger Band Squeeze
- Detects periods of low volatility
- Triggers trades on breakout from squeeze
- Confirms with ADX trend strength

### 2. RSI + MACD Combination
- Uses RSI for overbought/oversold conditions
- Confirms with MACD crossover
- Considers market volatility

### 3. ADX Trend Strength
- Measures trend strength
- Helps filter out weak signals
- Used as confirmation for other strategies

## Risk Management

- **Daily Trade Limit**: Maximum number of trades per day
- **Stop Loss**: Automatic sell at specified loss percentage
- **Take Profit**: Automatic sell at specified profit percentage
- **Position Sizing**: Calculates trade size based on account balance

## Logging

- **Trade Logs**: `trades.csv` contains detailed trade history
- **System Logs**: `trading_bot.log` contains operational logs
- **Color-coded Console Output**: Real-time trading signals and status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This trading bot is for educational purposes only. Use at your own risk. The developers are not responsible for any financial losses incurred while using this software.
