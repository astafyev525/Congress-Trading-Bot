from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import logging

logger = logging.getLogger(__name__)

class AlpacaClient:
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.client = TradingClient(api_key, secret_key, paper=paper)
    
    def buy_stock(self, symbol: str, amount: float):
        """Buy stock with dollar amount"""
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                notional=amount,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            order = self.client.submit_order(order_data)
            logger.info(f"Bought ${amount} of {symbol}")
            return order
        except Exception as e:
            logger.error(f"Failed to buy {symbol}: {e}")
            raise
    
    def get_positions(self):
        """Get current positions"""
        return self.client.get_all_positions()
    
    def get_account(self):
        """Get account info"""
        return self.client.get_account()

def test_alpaca_connection():
    """Test Alpaca connection"""
    from app.config import get_settings
    settings = get_settings()
    
    if not settings.ALPACA_API_KEY:
        print("No Alpaca API key found")
        return False
    
    try:
        client = AlpacaClient(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
        account = client.get_account()
        print(f"Connected to Alpaca: ${account.buying_power} buying power")
        return True
    except Exception as e:
        print(f"Alpaca connection failed: {e}")
        return False

if __name__ == "__main__":
    test_alpaca_connection()