import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

class RiskManager:
    def __init__(self):
        self.max_trades = int(os.getenv('MAX_TRADES_PER_DAY', 5))
        self.stop_loss = float(os.getenv('STOP_LOSS_PERCENTAGE', 2.0))
        self.take_profit = float(os.getenv('TAKE_PROFIT_PERCENTAGE', 3.0))
        self.trades_today = 0
        self.last_trade_date = None
        
    def can_trade(self):
        """Check if we can execute a new trade based on daily limits"""
        today = datetime.now().date()
        
        # Reset counter if it's a new day
        if self.last_trade_date != today:
            self.trades_today = 0
            self.last_trade_date = today
            
        if self.trades_today >= self.max_trades:
            logging.warning(f"Daily trade limit reached ({self.max_trades} trades)")
            return False
            
        return True
        
    def update_trade_count(self):
        """Update the trade counter after a successful trade"""
        self.trades_today += 1
        logging.info(f"Trade count updated: {self.trades_today}/{self.max_trades} trades today")
        
    def calculate_position_size(self, account_balance, risk_per_trade=0.01):
        """Calculate position size based on account balance and risk per trade"""
        try:
            position_size = account_balance * risk_per_trade
            logging.info(f"Calculated position size: {position_size:.8f}")
            return position_size
        except Exception as e:
            logging.error(f"Error calculating position size: {e}")
            return None

class DataProcessor:
    @staticmethod
    def clean_data(df):
        """Clean and prepare data for analysis"""
        try:
            # Remove any rows with NaN values
            df = df.dropna()
            
            # Ensure all numeric columns are float type
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        except Exception as e:
            logging.error(f"Error cleaning data: {e}")
            return None
            
    @staticmethod
    def calculate_volatility(df, window=20):
        """Calculate price volatility"""
        try:
            returns = df['close'].pct_change()
            volatility = returns.rolling(window=window).std()
            return volatility
        except Exception as e:
            logging.error(f"Error calculating volatility: {e}")
            return None
            
    @staticmethod
    def calculate_bollinger_bands(df, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        try:
            middle_band = df['close'].rolling(window=window).mean()
            std = df['close'].rolling(window=window).std()
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            return upper_band, middle_band, lower_band
        except Exception as e:
            logging.error(f"Error calculating Bollinger Bands: {e}")
            return None, None, None
            
    @staticmethod
    def calculate_keltner_channels(df, window=20, atr_mult=1.5):
        """Calculate Keltner Channels"""
        try:
            # Calculate ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            atr = true_range.rolling(window=window).mean()
            
            # Calculate Keltner Channels
            middle_line = df['close'].rolling(window=window).mean()
            upper_line = middle_line + (atr * atr_mult)
            lower_line = middle_line - (atr * atr_mult)
            
            return upper_line, middle_line, lower_line
        except Exception as e:
            logging.error(f"Error calculating Keltner Channels: {e}")
            return None, None, None
            
    @staticmethod
    def calculate_adx(df, period=14):
        """Calculate Average Directional Index (ADX)"""
        try:
            adx = talib.ADX(df['high'], df['low'], df['close'], timeperiod=period)
            return adx
        except Exception as e:
            logging.error(f"Error calculating ADX: {e}")
            return None

class TradeLogger:
    def __init__(self, log_file='trades.csv'):
        self.log_file = log_file
        self.ensure_log_file_exists()
        
    def ensure_log_file_exists(self):
        """Create log file if it doesn't exist"""
        if not os.path.exists(self.log_file):
            columns = ['timestamp', 'symbol', 'side', 'quantity', 'price', 'pnl', 'strategy']
            pd.DataFrame(columns=columns).to_csv(self.log_file, index=False)
            
    def log_trade(self, symbol, side, quantity, price, strategy, pnl=None):
        """Log a trade to the CSV file"""
        try:
            trade_data = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'strategy': strategy,
                'pnl': pnl
            }
            
            df = pd.DataFrame([trade_data])
            df.to_csv(self.log_file, mode='a', header=False, index=False)
            logging.info(f"Trade logged to {self.log_file}")
            
        except Exception as e:
            logging.error(f"Error logging trade: {e}")
            
    def get_trade_history(self, days=7):
        """Get trade history for the specified number of days"""
        try:
            df = pd.read_csv(self.log_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff_date = datetime.now() - timedelta(days=days)
            return df[df['timestamp'] >= cutoff_date]
        except Exception as e:
            logging.error(f"Error getting trade history: {e}")
            return None 