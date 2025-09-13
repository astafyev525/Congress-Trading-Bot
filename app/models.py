from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    politician_name = Column(String(100), nullable = False, index = False)
    chamber = Column(String(10), nullable = False)
    party = Column(String(20))
    state = Column(String(50))
    ticker = Column(String(10), nullable = False, index = True)
    company_name = Column(String(200))
    processed_for_trading = Column(Boolean, default=False)

    trade_type = Column(String(20), nullable = False)
    amount_range = Column(String(50))
    min_amount = Column(Float)
    max_amount = Column(Float)
    estimated_amount = Column(Float)

    transaction_date = Column(DateTime, nullable = False, index = True)
    disclosure_date = Column(DateTime, nullable = False)

    stock_price_at_trade = Column(Float)
    committees = Column(Text)

    disclosure_delay_days = Column(Integer)

    created_at = Column(DateTime, default = datetime.now(timezone.utc))
    updated_at = Column(DateTime, default = datetime.now(timezone.utc), onupdate = datetime.now(timezone.utc))

    source = Column(String(50), default = "FMP")

    def __repr__(self):
        return f"Trade {self.politician_name}: {self.trade_type} {self.ticker} ${self.estimated_amount}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "politician_name": self.politician_name,
            "chamber": self.chamber,
            "party": self.party,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "trade_type": self.trade_type,
            "amount_range": self.amount_range,
            "estimated_amount": self.estimated_amount,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "disclosure_date": self.disclosure_date.isoformat() if self.disclosure_date else None,
            "disclosure_delay_days": self.disclosure_delay_days,
            "stock_price_at_trade": self.stock_price_at_trade,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "state": self.state,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "committees": self.committees,
        }
class Politician(Base):
    __tablename__ = "politicians"
    id = Column(Integer, primary_key=True, index = True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    chamber = Column(String(10), nullable=False)
    party = Column(String(20))
    state = Column(String(50))
    district = Column(String(10))

    committees = Column(Text)
    leadership_positions = Column(Text)

    total_trades = Column(Integer, default = 0)
    total_estimated_volume = Column(Float, default = 0.0)
    average_trade_size = Column(Float, default = 0.0)
    last_trade_date = Column(DateTime)

    bio_url = Column(String(500))
    twitter_handle = Column(String(50))

    created_at = Column(DateTime, default = datetime.now(timezone.utc))
    updated_at = Column(DateTime, default = datetime.now(timezone.utc), onupdate = datetime.now(timezone.utc))

    def __repr__(self):
        return f"Politician: {self.name} ({self.chamber} -- {self.party})"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "chamber": self.chamber,
            "party": self.party,
            "state": self.state,
            "district": self.district,
            "total_trades": self.total_trades,
            "total_estimated_volume": self.total_estimated_volume,
            "average_trade_size": self.average_trade_size,
            "last_trade_date": self.last_trade_date.isoformat() if self.last_trade_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "committees": self.committees
        }
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(100), nullable = False, unique = True, index = True)

    hashed_password = Column(String(255), nullable=False)

    full_name = Column(String(100))
    organization = Column(String(100))

    is_active = Column(Boolean, default = True)
    is_admin = Column(Boolean, default = False)
    is_premium = Column(Boolean, default = False)

    api_calls_today = Column(Integer, default = 0)
    api_call_total = Column(Integer, default = 0)
    daily_rate_limit = Column(Integer, default = 1000)
    last_api_call = Column(DateTime)

    subscription_tier = Column(String(20), default = "free")
    subscription_expires = Column(DateTime)

    created_at = Column(DateTime, default = datetime.now(timezone.utc))
    last_login = Column(DateTime)
    updated_at = Column(DateTime, default = datetime.now(timezone.utc), onupdate= datetime.now(timezone.utc))

    def __repr__(self):
        return f"User {self.email} ({'Active' if self.is_active else 'Inactive'})"
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "organization": self.organization,
            "is_active": self.is_active,
            "is_premium": self.is_premium,
            "subscription_tier": self.subscription_tier,
            "api_calls_today": self.api_calls_today,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
class TradingAccount(Base):
       __tablename__ = "trading_accounts"
       id = Column(Integer, primary_key=True, index=True)
       user_id = Column(Integer, ForeignKey("users.id"))
       alpaca_api_key = Column(String(255))
       alpaca_secret_key = Column(String(255))
       account_type = Column(String(20), default="paper")
       is_active = Column(Boolean, default=True)
       created_at = Column(DateTime, default=datetime.now(timezone.utc))
class BotTrade(Base):
       __tablename__ = "bot_trades"
       id = Column(Integer, primary_key=True, index=True)
       user_id = Column(Integer, ForeignKey("users.id"))
       congressional_trade_id = Column(Integer, ForeignKey("trades.id"))
       symbol = Column(String(10), nullable=False)
       side = Column(String(10), nullable=False)
       quantity = Column(Float)
       price = Column(Float)
       alpaca_order_id = Column(String(100))
       profit_loss = Column(Float, default=0.0)
       created_at = Column(DateTime, default=datetime.now(timezone.utc))

class BotSettings(Base):
       __tablename__ = "bot_settings"
       id = Column(Integer, primary_key=True, index=True)
       user_id = Column(Integer, ForeignKey("users.id"))
       is_active = Column(Boolean, default=False)
       max_trade_amount = Column(Float, default=1000.0)
       follow_politicians = Column(Text)  # JSON string
       strategy = Column(String(50), default="copy_trades")
       updated_at = Column(DateTime, default=datetime.now(timezone.utc))