import os
import logging
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from utils import RiskManager, DataProcessor, TradeLogger
import talib
from config_validator import ConfigValidator
from colorama import init, Fore, Back, Style

# Initialize colorama for Windows
init(autoreset=True)

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    FORMATS = {
        logging.DEBUG: Style.DIM + format_str,
        logging.INFO: format_str,
        logging.WARNING: Fore.YELLOW + format_str,
        logging.ERROR: Fore.RED + format_str,
        logging.CRITICAL: Back.RED + Fore.WHITE + format_str
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# File handler for keeping normal logs without colors
file_handler = logging.FileHandler('trading_bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Load and validate environment variables
load_dotenv()
ConfigValidator.validate_config()

class BinanceTrader:
    def __init__(self):
        try:
            self.api_key = os.getenv('BINANCE_API_KEY')
            self.api_secret = os.getenv('BINANCE_SECRET_KEY')
            self.symbol = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
            self.interval = os.getenv('TRADING_INTERVAL', '1h')
            self.quantity = float(os.getenv('TRADING_QUANTITY', '0.001'))
            
            # Strategy parameters
            self.bb_window = int(os.getenv('BB_WINDOW', 20))
            self.bb_std = float(os.getenv('BB_STD', 2.0))
            self.keltner_window = int(os.getenv('KELTNER_WINDOW', 20))
            self.keltner_atr_mult = float(os.getenv('KELTNER_ATR_MULT', 1.5))
            self.adx_period = int(os.getenv('ADX_PERIOD', 14))
            self.adx_threshold = float(os.getenv('ADX_THRESHOLD', 25))
            
            # RSI and MACD parameters
            self.rsi_period = int(os.getenv('RSI_PERIOD', 14))
            self.macd_fast = int(os.getenv('MACD_FAST', 12))
            self.macd_slow = int(os.getenv('MACD_SLOW', 26))
            self.macd_signal = int(os.getenv('MACD_SIGNAL', 9))
            
            if not self.api_key or not self.api_secret:
                raise ValueError("API keys not found in environment variables")
                
            self.client = Client(self.api_key, self.api_secret)
            self.risk_manager = RiskManager()
            self.trade_logger = TradeLogger()
            logging.info("Binance client initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing Binance client: {e}")
            raise
        
    def get_historical_klines(self, symbol, interval, lookback):
        """Get historical klines/candlestick data"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback)
            
            logging.info(f"Fetching historical data for {symbol} from {start_time} to {end_time}")
            
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_str=end_time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            # Clean and process data
            df = DataProcessor.clean_data(df)
            
            # Calculate all indicators
            df['volatility'] = DataProcessor.calculate_volatility(df)
            df['upper_bb'], df['middle_bb'], df['lower_bb'] = DataProcessor.calculate_bollinger_bands(
                df, self.bb_window, self.bb_std)
            df['upper_kc'], df['middle_kc'], df['lower_kc'] = DataProcessor.calculate_keltner_channels(
                df, self.keltner_window, self.keltner_atr_mult)
            df['adx'] = DataProcessor.calculate_adx(df, self.adx_period)
            
            # Calculate RSI and MACD
            df['rsi'] = talib.RSI(df['close'], timeperiod=self.rsi_period)
            df['macd'], df['signal'], _ = talib.MACD(
                df['close'], 
                fastperiod=self.macd_fast,
                slowperiod=self.macd_slow,
                signalperiod=self.macd_signal
            )
            
            # Detect Bollinger Band Squeeze
            df['squeeze'] = (df['upper_bb'] < df['upper_kc']) & (df['lower_bb'] > df['lower_kc'])
                
            logging.info(f"Successfully fetched {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logging.error(f"Error fetching historical data: {e}")
            return None
    
    def log_signal(self, signal_type, reason):
        """Log trading signals with colors"""
        if signal_type == "BUY":
            logging.info(f"{Fore.GREEN}[BUY] {reason}")
        elif signal_type == "SELL":
            logging.info(f"{Fore.RED}[SELL] {reason}")
        elif signal_type == "HOLD":
            logging.info(f"{Fore.YELLOW}[HOLD] {reason}")

    def log_trade_execution(self, side, quantity, price, status="PENDING"):
        """Log trade execution with colors"""
        if status == "PENDING":
            color = Fore.YELLOW
            status_symbol = "[PENDING]"
        elif status == "SUCCESS":
            color = Fore.GREEN
            status_symbol = "[SUCCESS]"
        else:  # FAILED
            color = Fore.RED
            status_symbol = "[FAILED]"
            
        logging.info(f"{color}{status_symbol} {side} TRADE: {quantity} {self.symbol} @ {price}")

    def execute_trade(self, symbol, side, quantity, strategy):
        """Execute a trade on Binance"""
        try:
            if not self.risk_manager.can_trade():
                self.log_signal("HOLD", "Daily trade limit reached")
                return None
                
            # Get current price for logging
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            self.log_trade_execution(side, quantity, current_price, "PENDING")
            
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            # Update trade count and log the trade
            self.risk_manager.update_trade_count()
            self.trade_logger.log_trade(symbol, side, quantity, current_price, strategy)
            
            self.log_trade_execution(side, quantity, current_price, "SUCCESS")
            return order
            
        except Exception as e:
            self.log_trade_execution(side, quantity, current_price, "FAILED")
            logging.error(f"Error executing trade: {str(e)}", exc_info=True)
            return None

    def run_strategy(self):
        """Run the trading strategy"""
        try:
            # Get historical data
            df = self.get_historical_klines(self.symbol, self.interval, 30)
            if df is None:
                logging.error("Failed to get historical data")
                return
            
            # Get current values
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Log current market conditions with colors
            logging.info(f"\n{Fore.CYAN}=== Current Market Conditions ===")
            logging.info(f"Price: {Fore.CYAN}{current['close']:.2f}")
            
            # Color code RSI
            rsi_color = Fore.GREEN if current['rsi'] < 30 else Fore.RED if current['rsi'] > 70 else Fore.YELLOW
            logging.info(f"RSI: {rsi_color}{current['rsi']:.2f}")
            
            # Color code MACD
            macd_color = Fore.GREEN if current['macd'] > current['signal'] else Fore.RED
            logging.info(f"MACD: {macd_color}{current['macd']:.2f}")
            logging.info(f"Signal: {macd_color}{current['signal']:.2f}")
            
            # Color code ADX
            adx_color = Fore.GREEN if current['adx'] > self.adx_threshold else Fore.YELLOW
            logging.info(f"ADX: {adx_color}{current['adx']:.2f}")
            
            # Check for Bollinger Band Squeeze strategy
            squeeze_now = current['squeeze']
            squeeze_prev = previous['squeeze']
            
            if squeeze_prev and not squeeze_now and current['adx'] > self.adx_threshold:
                if current['close'] > current['upper_bb']:
                    self.log_signal("BUY", "Upward breakout from BB squeeze")
                    self.execute_trade(self.symbol, SIDE_BUY, self.quantity, "BB_SQUEEZE")
                elif current['close'] < current['lower_bb']:
                    self.log_signal("SELL", "Downward breakout from BB squeeze")
                    self.execute_trade(self.symbol, SIDE_SELL, self.quantity, "BB_SQUEEZE")
            
            # Check for RSI + MACD strategy
            if (current['rsi'] < 30 and current['macd'] > current['signal'] and 
                current['volatility'] < df['volatility'].mean()):
                self.log_signal("BUY", "RSI oversold with MACD confirmation")
                self.execute_trade(self.symbol, SIDE_BUY, self.quantity, "RSI_MACD")
            elif (current['rsi'] > 70 and current['macd'] < current['signal'] and 
                  current['volatility'] < df['volatility'].mean()):
                self.log_signal("SELL", "RSI overbought with MACD confirmation")
                self.execute_trade(self.symbol, SIDE_SELL, self.quantity, "RSI_MACD")
            else:
                self.log_signal("HOLD", "No clear signals")
                
        except Exception as e:
            logging.error(f"Error in strategy execution: {e}")
            logging.error(f"Error details: {str(e)}", exc_info=True)

def main():
    try:
        # Load configuration from environment variables
        analysis_interval = int(os.getenv('ANALYSIS_INTERVAL_MINUTES', 15)) * 60  # Convert to seconds
        max_retries = int(os.getenv('MAX_RETRIES', 3))
        retry_delay = int(os.getenv('RETRY_DELAY_SECONDS', 60))
        
        trader = BinanceTrader()
        retry_count = 0
        
        logging.info(f"{Fore.CYAN}Starting trading bot with analysis interval of {analysis_interval/60} minutes")
        
        while True:
            try:
                trader.run_strategy()
                retry_count = 0  # Reset retry count on successful run
                logging.info(f"{Fore.CYAN}Analysis completed. Next analysis in {analysis_interval/60} minutes...")
                time.sleep(analysis_interval)
                
            except Exception as e:
                retry_count += 1
                logging.error(f"Error in analysis cycle: {e}")
                
                if retry_count >= max_retries:
                    logging.error(f"Max retries ({max_retries}) reached. Stopping bot.")
                    break
                    
                logging.info(f"Retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(retry_delay)
                
    except KeyboardInterrupt:
        logging.info(f"{Fore.YELLOW}Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error in main loop: {e}")
    finally:
        logging.info(f"{Fore.YELLOW}Trading bot stopped")

if __name__ == "__main__":
    main() 