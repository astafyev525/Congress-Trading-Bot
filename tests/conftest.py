import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models import User, Trade, Politician
from app.auth import get_password_hash, create_access_token
from app.config import get_settings

SQLALCHAMEY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHAMEY_DATABASE_URL,
    connect_args = {"check_same_thread": False},
    poolclass = StaticPool
)


TestingSessionLocal = sessionmaker(autocommit = False, autoflush= False, bind = engine)

@pytest.fixture(scope = "function")
def db_session():
    Base.metadata.create_all(bind = engine)
    session = TestingSessionLocal

    try:
        yield session
    finally:
        session.close()

        Base.metadata.drop_all(bind = engine)

@pytest.fixture(scope = "function")
def cient(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture(scope = "function")
def test_user(db_session):
    user = User(
        email = "test@example.com",
        hashed_password = get_password_hash("testpassword123"),
        full_name = "Test User",
        is_active = True
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope = "function")
def auth_headers(test_user):
    token = create_access_token(data = {"sub", test_user.email})

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope = "function")
def sample_politician(db_session):
    politician = Politician(
        name = "Nancy Pelosi",
        chamber = "House",
        party = "Democratic",
        state = "CA",
        total_trades = 5,
        total_estimated_volume = 150000.0,
        average_trade_size = 30000.0
    )

    db_session.add(politician)
    db_session.commit()
    db_session.refresh(politician)

    return politician

@pytest.fixture(scope = "function")
def sample_trades(db_session, sample_politician):
    from datetime import datetime, timezone
    trades = [
        Trade(
            politician_name = "Nancy Pelosi",
            chamber = "House",
            party = "Democratic",
            ticker = "APPL",
            trade_type = "Buy",
            estimated_amount = 25000.0,
            transaction_date = datetime(2024, 1, 15),
            discolusure_date = datetime(2024, 2, 1),
            disclosure_delay_days = 17,
            source = "Test"
        ),
        Trade(
            politician_name = "Nancy Pelosi",
            chamber = "House",
            party = "Democratic",
            ticker = "MSFT",
            trade_type = "Sell",
            estimated_amount = 35000.0,
            transaction_date = datetime(2024, 1, 20),
            disclosure_data = datetime(2024, 2, 5),
            disclosure_delay_days = 16,
            source = "Test"
        )
    ]
    for trade in trades:
        db_session.add(trade)

    db_session.commit()

    for trade in trades:
        db_session.refresh(trade)

    return trades

@pytest.fixture(scope = "session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_fmp_data():
    from app.fmp_client import TradeData
    from datetime import datetime

    return [
        TradeData(
            politician_name="Test Politician",
            chamber = "House",
            ticker = "GOOGL",
            trade_type = "Buy",
            amount = 50000.0,
            transaction_date= datetime(2024,1,10),
            disclosure_date=datetime(2024,1,25)
        ),
        TradeData(
            politician_name="Another Politician",
            chamber = "Senate",
            ticker = "TSLA",
            trade_type = "Sell",
            amount = 75000.0,
            transaction_date=datetime(2024,1,12),
            disclosure_date=datetime(2024,1,28)
        )
    ]
