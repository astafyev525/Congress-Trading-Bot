from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_active_user
from app.models import User, BotSettings, TradingAccount, BotTrade
from app.trading_service import TradingService
import json

router = APIRouter(prefix="/api/trading", tags=["Trading Bot"])

class AlpacaAccountCreate(BaseModel):
    api_key: str
    secret_key: str

@router.post("/account/connect")
async def connect_alpaca_account(
    account_data: AlpacaAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Connect user's Alpaca account"""
    
   
    from app.alpaca_client import AlpacaClient
    try:
        client = AlpacaClient(account_data.api_key, account_data.secret_key)
        client.get_account()  
    except Exception as e:
        raise HTTPException(400, f"Invalid Alpaca credentials: {e}")
    
    
    existing = db.query(TradingAccount).filter_by(user_id=current_user.id).first()
    if existing:
        existing.alpaca_api_key = account_data.api_key
        existing.alpaca_secret_key = account_data.secret_key
    else:
        trading_account = TradingAccount(
            user_id=current_user.id,
            alpaca_api_key=account_data.api_key,
            alpaca_secret_key=account_data.secret_key
        )
        db.add(trading_account)
    
    db.commit()
    return {"message": "Alpaca account connected successfully"}

@router.post("/bot/start")
async def start_bot(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start trading bot"""
    
  
    if not db.query(TradingAccount).filter_by(user_id=current_user.id).first():
        raise HTTPException(400, "Please connect Alpaca account first")
    
    settings = db.query(BotSettings).filter_by(user_id=current_user.id).first()
    if not settings:
        settings = BotSettings(
            user_id=current_user.id,
            follow_politicians=json.dumps(["Nancy Pelosi"]) 
        )
        db.add(settings)
    
    settings.is_active = True
    db.commit()
    
    return {"message": "Trading bot started", "status": "active"}

@router.get("/bot/status")
async def get_bot_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get bot status"""
    
    settings = db.query(BotSettings).filter_by(user_id=current_user.id).first()
    trades = db.query(BotTrade).filter_by(user_id=current_user.id).all()
    
    total_pnl = sum(trade.profit_loss or 0 for trade in trades)
    
    return {
        "is_active": settings.is_active if settings else False,
        "total_trades": len(trades),
        "total_pnl": total_pnl,
        "followed_politicians": json.loads(settings.follow_politicians) if settings else []
    }