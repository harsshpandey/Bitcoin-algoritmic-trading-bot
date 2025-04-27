import os
from dotenv import load_dotenv
import logging

class ConfigValidator:
    REQUIRED_VARS = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY',
        'TRADING_SYMBOL',
        'TRADING_INTERVAL',
        'TRADING_QUANTITY',
        'MAX_TRADES_PER_DAY',
        'STOP_LOSS_PERCENTAGE',
        'TAKE_PROFIT_PERCENTAGE'
    ]

    OPTIONAL_VARS = {
        'BB_WINDOW': '20',
        'BB_STD': '2.0',
        'KELTNER_WINDOW': '20',
        'KELTNER_ATR_MULT': '1.5',
        'ADX_PERIOD': '14',
        'ADX_THRESHOLD': '25',
        'RSI_PERIOD': '14',
        'MACD_FAST': '12',
        'MACD_SLOW': '26',
        'MACD_SIGNAL': '9'
    }

    @staticmethod
    def validate_config():
        """Validate all required environment variables are set"""
        load_dotenv()
        missing_vars = []
        invalid_vars = []

        # Check required variables
        for var in ConfigValidator.REQUIRED_VARS:
            if not os.getenv(var):
                missing_vars.append(var)

        # Check optional variables and set defaults if missing
        for var, default in ConfigValidator.OPTIONAL_VARS.items():
            if not os.getenv(var):
                os.environ[var] = default
                logging.info(f"Setting default value for {var}: {default}")

        # Validate numeric values
        numeric_vars = {
            'TRADING_QUANTITY': float,
            'MAX_TRADES_PER_DAY': int,
            'STOP_LOSS_PERCENTAGE': float,
            'TAKE_PROFIT_PERCENTAGE': float,
            'BB_WINDOW': int,
            'BB_STD': float,
            'KELTNER_WINDOW': int,
            'KELTNER_ATR_MULT': float,
            'ADX_PERIOD': int,
            'ADX_THRESHOLD': float,
            'RSI_PERIOD': int,
            'MACD_FAST': int,
            'MACD_SLOW': int,
            'MACD_SIGNAL': int
        }

        for var, var_type in numeric_vars.items():
            try:
                value = os.getenv(var)
                if value:
                    var_type(value)
            except (ValueError, TypeError):
                invalid_vars.append(f"{var} (expected {var_type.__name__})")

        # Validate trading interval
        valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        if os.getenv('TRADING_INTERVAL') not in valid_intervals:
            invalid_vars.append('TRADING_INTERVAL (invalid interval)')

        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        if invalid_vars:
            raise ValueError(f"Invalid environment variables: {', '.join(invalid_vars)}")

        logging.info("Configuration validation successful")
        return True

if __name__ == "__main__":
    try:
        ConfigValidator.validate_config()
        print("Configuration is valid!")
    except ValueError as e:
        print(f"Configuration error: {e}")
        exit(1) 