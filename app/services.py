import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.database import get_db
from app.models import Trade, Politician, User
from app.fmp_client import FMPClient, TradeData
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class TradeService:

    @staticmethod
    def sync_trades_from_fmp(db: Session, limit_per_chamber: int = 100) -> Dict[str, Any]:
        logger.info(f"Starting trade sunc from FMP (limit: {limit_per_chamber} per chamber)")
        sync_stats = {
            "started_at": datetime.now(timezone.utc),
            "trades_fetched": 0,
            "trades_stored": 0,
            "trades_updated": 0,
            "politicians_created": 0,
            "politicians_updated": 0,
            "errors": [],
            "success": False
        }

    
        try:
            logger.info("Fetching trades from FMP API")
            import asyncio
            from app.fmp_client import FMPClient
            
            # Create event loop and run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                async def fetch_data():
                    async with FMPClient(settings.FMP_API_KEY) as client:
                        return await client.get_all_trades(limit_per_chamber=limit_per_chamber)
                
                trades_data = loop.run_until_complete(fetch_data())
            finally:
                loop.close()

            sync_stats["trades_fetched"] = len(trades_data)

            if not trades_data:
                logger.warning("No trades returned by FMP API")
                sync_stats["errors"].append("No trades returned from FMP API")
                return sync_stats
            
            logger.info(f"Fetched {len(trades_data)} from FMP")

            for trade_data in trades_data:
                try:
                    politician = TradeService._get_or_create_politician(
                        db, trade_data.politician_name, trade_data.chamber
                    )
                    if not hasattr(politician, "_is_new"):
                        sync_stats["politicians_created"] +=1
                    else:
                        sync_stats["politicians_updated"] +=1

                    existing_trade = db.query(Trade).filter(
                        and_(
                            Trade.politician_name == trade_data.politician_name,
                            Trade.ticker == trade_data.ticker,
                            Trade.transaction_date == trade_data.transaction_date,
                            Trade.disclosure_date == trade_data.disclosure_date
                        )
                    ).first()

                    if existing_trade:
                        TradeService._update_trade_from_data(existing_trade, trade_data)
                        sync_stats["trades_updated"] +=1
                        logger.debug(f"Updated existing trade: {trade_data.politician_name} - {trade_data.ticker}")
                    else:
                        new_trade = TradeService._create_trade_from_data(trade_data)
                        db.add(new_trade)
                        sync_stats["trades_stored"] +=1
                        logger.debug(f"Created new trade: {trade_data.politician_name} - {trade_data.ticker}")

                except Exception as e:
                    error_msg = f"Error processing trade {trade_data.politician_name} - {trade_data.ticker}: {str(e)}"
                    logger.error(error_msg)
                    sync_stats["errors"].append(error_msg)
                    continue

            TradeService._update_politician_stats(db)

            db.commit()

            sync_stats["completed_at"] = datetime.now(timezone.utc)
            sync_stats["duration_seconds"] = (
                sync_stats["completed_at"] - sync_stats["started_at"]
            ).total_seconds()

            sync_stats["success"] = True

            logger.info(f"Trade sync completed {sync_stats['trades_stored']} new , {sync_stats['trades_updated']} updated")

        except Exception as e:
            db.rollback()
            error_msg = f"Trade sync failed: {str(e)}"
            logger.error(error_msg)
            sync_stats["errors"].append(error_msg)
            sync_stats["completed_at"] = datetime.now(timezone.utc)

        return sync_stats

    @staticmethod
    def _get_or_create_politician(db: Session, name: str, chamber: str) -> Politician:
        politician = db.query(Politician).filter(Politician.name == name).first()
        
        if not politician:
            politician = Politician(
                name = name,
                chamber = chamber,
                created_at = datetime.now(timezone.utc)
            )

            db.add(politician)
            db.flush()
            politician._is_new = True
            logger.info(f"Created new politician: {name} ({chamber})")

        return politician
    
    @staticmethod
    def _create_trade_from_data(trade_data: TradeData) -> Trade:
        disclosure_delay = (trade_data.disclosure_date - trade_data.transaction_date).days

        return Trade(
            politician_name = trade_data.politician_name,
            chamber = trade_data.chamber,
            ticker = trade_data.ticker,
            trade_type = trade_data.trade_type,

            estimated_amount = trade_data.amount,

            transaction_date = trade_data.transaction_date,
            disclosure_date = trade_data.disclosure_date,
            disclosure_delay_days = disclosure_delay,

            source = "FMP",
            created_at = datetime.now(timezone.utc)
        )
    
    @staticmethod
    def _update_trade_from_data(existing_trade: Trade, trade_data: TradeData):
        existing_trade.estimated_amount = trade_data.amount
        existing_trade.trade_type = trade_data.trade_type
        existing_trade.updated_at = datetime.now(timezone.utc)

        disclosure_delay = (trade_data.disclosure_date - trade_data.transaction_date).days
        existing_trade.disclosure_delay_days = disclosure_delay

    @staticmethod
    def _update_politician_stats(db: Session):
        logger.info("Updating politician statistics...")

        politicians = db.query(Politician).all()

        for politician in politicians:
            trades = db.query(Trade).filter(Trade.politician_name == politician.name).all()
            if trades:
                politician.total_trades = len(trades)
                politician.total_estimated_volume = sum(trade.estimated_amount or 0 for trade in trades)
                politician.average_trade_size = politician.total_estimated_volume / politician.total_trades
                politician.last_trade_date = max(trade.transaction_date for trade in trades)

            else:
                politician.total_trades = 0
                politician.total_estimated_volume = 0.0
                politician.average_trade_size = 0.0
                politician.last_trade_date = None

            politician.updated_at = datetime.now(timezone.utc)

        logger.info(f"Updated statistics for {len(politicians)} politicians")

class PoliticianService:
    @staticmethod
    def get_top_traders(db: Session, limit: int = 10) -> List[Politician]:
        return db.query(Politician).filter(
            Politician.total_estimated_volume > 0
        ).order_by(
            desc(Politician.total_estimated_volume)
        ).limit(limit).all()

    @staticmethod
    def get_recent_traders(db: Session, days: int = 30, limit: int = 10) -> List[Politician]:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days = days)
        return db.query(Politician).filter(
            Politician.last_trade_date > cutoff_date
        ).order_by(
            desc(Politician.last_trade_date)
        ).limit(limit).all()
    
def test_trade_service():
    print("Testing...")

    try:
        from app.database import SessionLocal
        db = SessionLocal()

        result = TradeService.sync_trades_from_fmp(db, limit_per_chamber=5)
        print("Sync completed")

        print(f"Trades fetched: {result['trades_fetched']}")
        print(f"   Trades stored: {result['trades_stored']}")
        print(f"   Politicians created: {result['politicians_created']}")
        print(f"   Success: {result['success']}")

        if result['errors']:
            print(f"Errors {result['errors']}")
        db.close()

        return True
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_trade_service()
    
