from dotenv import load_dotenv
import os
import sys
from binance.client import Client
from binance.exceptions import BinanceAPIException

def verify_env():
    try:
        # Load environment variables
        load_dotenv()
        
        print("\n=== Environment Variables Verification ===\n")
        
        # Check if .env file exists
        if not os.path.exists('.env'):
            print("❌ .env file not found in the current directory")
            return False
            
        # Check required variables
        required_vars = {
            'BINANCE_API_KEY': 'Binance API Key',
            'BINANCE_SECRET_KEY': 'Binance Secret Key',
            'TRADING_SYMBOL': 'Trading Symbol',
            'TRADING_INTERVAL': 'Trading Interval',
            'TRADING_QUANTITY': 'Trading Quantity'
        }
        
        all_vars_present = True
        
        # Check each required variable
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # For API keys, only show last 4 characters for security
                if 'KEY' in var:
                    print(f"{description}: {'*' * 4}{value[-4:] if len(value) > 4 else '*' * len(value)}")
                else:
                    print(f"{description}: {value}")
            else:
                print(f"{description}: ❌ NOT FOUND")
                all_vars_present = False
        
        if not all_vars_present:
            print("\n❌ Some required environment variables are missing")
            return False
            
        # Check if we can connect to Binance
        try:
            print("\nAttempting to connect to Binance API...")
            client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'))
            
            # Test API connection
            try:
                if client.ping():
                    print("✅ Binance API Connection: SUCCESSFUL")
                    
                    # Test if we can get account info (to verify API permissions)
                    try:
                        account_info = client.get_account()
                        print("✅ API Permissions: SUCCESSFUL (Can access account info)")
                        return True
                    except BinanceAPIException as e:
                        print(f"⚠️ API Permissions: LIMITED - Error Code: {e.code}, Message: {e.message}")
                        return True
                    except Exception as e:
                        print(f"⚠️ API Permissions: LIMITED - {str(e)}")
                        return True
                else:
                    print("❌ Binance API Connection: FAILED")
                    return False
                    
            except BinanceAPIException as e:
                print(f"❌ Binance API Error: Code {e.code} - {e.message}")
                return False
                
        except Exception as e:
            print(f"❌ Connection Error: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_env()
    if not success:
        sys.exit(1) 