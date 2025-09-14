import logging
from sqlalchemy.orm import Session
from app.models import Trade, User, BotTrade, BotSettings, TradingAccount
from app.alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

class TradingService:
    
    @staticmethod
    def process_new_congressional_trade(trade: Trade, db: Session):
        """Process new congressional trade for all active bots"""
        
       
        active_users = db.query(User).join(BotSettings).join(TradingAccount).filter(
            BotSettings.is_active == True,
            TradingAccount.is_active == True
        ).all()
        
        logger.info(f"Processing trade {trade.politician_name} {trade.ticker} for {len(active_users)} users")
        
        for user in active_users:
            try:
                if TradingService.should_copy_trade(trade, user.bot_settings):
                    TradingService.execute_copy_trade(trade, user, db)
            except Exception as e:
                logger.error(f"Failed to process trade for user {user.id}: {e}")
    
    @staticmethod
    def should_copy_trade(trade: Trade, settings: BotSettings) -> bool:
        """Decide if we should copy this trade"""
        
        
        import json
        try:
            followed = json.loads(settings.follow_politicians or "[]")
        except:
            followed = []
        
        
        if trade.politician_name not in followed:
            return False
        
        
        if trade.trade_type.lower() != "buy":
            return False
            
        
        if trade.estimated_amount < 15000:
            return False
            
        return True
    
    @staticmethod
    def execute_copy_trade(trade: Trade, user: User, db: Session):
        """Execute the actual trade via Alpaca"""
        
        try:
            
            trading_account = user.trading_account
            if not trading_account:
                logger.error(f"User {user.id} has no trading account")
                return
            
           
            alpaca = AlpacaClient(
                trading_account.alpaca_api_key,
                trading_account.alpaca_secret_key,
                paper=True
            )
            
            
            trade_amount = min(
                user.bot_settings.max_trade_amount,
                trade.estimated_amount * 0.1
            )
            
           
            order = alpaca.buy_stock(trade.ticker, trade_amount)
            
          
            bot_trade = BotTrade(
                user_id=user.id,
                congressional_trade_id=trade.id,
                symbol=trade.ticker,
                side="buy",
                quantity=float(order.qty) if order.qty else 0,
                price=float(order.filled_avg_price) if order.filled_avg_price else 0,
                alpaca_order_id=str(order.id)
            )
            db.add(bot_trade)
            db.commit()
            
            logger.info(f"Executed copy trade: User {user.id} bought ${trade_amount} of {trade.ticker}")
            
        except Exception as e:
            logger.error(f"Failed to execute copy trade: {e}")
            raise