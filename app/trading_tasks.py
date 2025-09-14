from app.tasks import celery_app
from app.database import SessionLocal
from app.models import Trade
from app.trading_service import TradingService
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.trading_tasks.process_new_congressional_trades")
def process_new_congressional_trades():
    """Process new congressional trades for trading bots"""
    
    db = SessionLocal()
    try:
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        new_trades = db.query(Trade).filter(
            Trade.created_at > cutoff,
            Trade.processed_for_trading == False
        ).all()
        
        logger.info(f"Processing {len(new_trades)} new congressional trades")
        
        for trade in new_trades:
            TradingService.process_new_congressional_trade(trade, db)
            trade.processed_for_trading = True
        
        db.commit()
        logger.info("✅ Congressional trades processed successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to process congressional trades: {e}")
        raise
    finally:
        db.close()