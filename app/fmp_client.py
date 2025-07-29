import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import time

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

class TradeData:
    def __init__(self, politician_name, chamber, ticker, trade_type, amount, transaction_date, disclosure_date):
        self.politician_name = politician_name
        self.chamber = chamber
        self.ticker = ticker
        self.trade_type = trade_type
        self.amount = amount
        self.transaction_date = transaction_date
        self.disclosure_date = disclosure_date
        self.source = "FMP"

class FMPClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.FMP_API_KEY
        self.base_url = "https://financialmodelingprep.com/api" 
        self.session = None
        self.requests_made = 0
        self.daily_limit = 200
        self.last_request_time = 0
        self.min_request_interval = 1.0
        self.cache = {}
        self.cache_ttl = 3600

        if not self.api_key:
            logger.warning("No api key found, will use mock data")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    def _is_cache_valid(self, cache_entry: dict) -> bool:
        age = time.time() - cache_entry['timestamp']
        return age < self.cache_ttl
    async def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def _make_request(self, endpoint: str, params: dict = None) -> dict:
        if not self.api_key:
            logger.warning("No API key")
            return self._get_mock_data(endpoint)
        
        if self.requests_made >= self.daily_limit:
            logger.error(f"Daily API limit reached {self.daily_limit}")
            raise Exception("Daily API limit exceeded")
        
        cache_key = f"{endpoint}_{params}"

        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.debug(f"Cache hit for {endpoint}")
            return self.cache[cache_key]['data']
        await self._rate_limit()

        params = params or {}

        params['apikey'] = self.api_key

        url = f"{self.base_url}/{endpoint}"

        try:
            logger.info(f"Making FMP Api request: {endpoint}")

            async with self.session.get(url, params = params) as response:
                self.requests_made +=1
                if response.status == 200:
                    data = await response.json()

                    self.cache[cache_key] = {
                        'data': data,
                        'timestamp': time.time()
                    }

                    logger.info(f"FMP Api success: {len(data)} records returned")
                    return data
                elif response.status == 429:
                    logger.warning("Rate limit hit - waiting 60 seconds")
                    await asyncio.sleep(60)
                    return await self._make_request(endpoint, params)
                else:
                    error_text = await response.text()
                    logger.error(f"FMP API error: {response.status}: {error_text}")
                    raise Exception(f"FMP API error: {response.status}")
        except Exception as e:
            logger.error(f"Failed to call FMP API: {e}")
            raise
    def _get_mock_data(self, endpoint: str) -> List[dict]:
        if "senate-trading" in endpoint:
            return[
                {
                    "representative": "Hon. Chuck Schumer",
                    "transaction": "Purchase", 
                    "ticker": "AAPL",
                    "transactionDate": "2025-01-15",
                    "publicationDate": "2025-02-01",
                    "amount": "$1,001 - $15,000"
                },
                {
                    "representative": "Hon. Susan Collins",
                    "transaction": "Sale",
                    "ticker": "MSFT", 
                    "transactionDate": "2025-01-20",
                    "publicationDate": "2025-02-05",
                    "amount": "$15,001 - $50,000"
                }
            ]
        elif "house-trading" in endpoint:
            return [
                {
                    "representative": "Hon. Nancy Pelosi",
                    "transaction": "Purchase",
                    "ticker": "GOOGL",
                    "transactionDate": "2025-01-10",
                    "publicationDate": "2025-01-30",
                    "amount": "$50,001 - $100,000"
                }
            ]
        
        return []
    
    async def get_senate_trades(self, limit: int = 100)->List[TradeData]:
        try:
            logger.info(f"Fetching Senate trades (limit: {limit})")
            raw_data = await self._make_request(
                "v4/senate-trading",
                params = {"limit": min(limit, 100)}
            )

            trades  =[]
            for item in raw_data:
                try:
                    trade = self._transform_trade_data(item, "Senate")
                    if trade:
                        trades.append(trade)
                except Exception as e:
                    logger.warning(f"Failed to transform senate trade{e}")
                    continue

            logger.info(f"Successfully processed {len(trades)} trades")
            return trades
        except Exception as e:
            logger.error(f"Failed to fetch Senate trades: {e}")
            return []
    
    async def get_house_trades(self, limit: int = 100)->List[TradeData]:
        try:
            logger.info(f"Fetching House trades (limit: {limit})")
            raw_data = await self._make_request(
                "v4/house-trading",
                params = {"limit": min(limit, 100)}
            )
            trades =  []
            for item in raw_data:
                try:
                    trade = self._transform_trade_data(item, "House")
                    if trade:
                        trades.append(trade)

                except Exception as e:
                    logger.warning(f"Failed to transform House trade: {e}")
                    continue
            logger.info(f"Successfully processed {len(trades)} trades")
            return trades
        except Exception as e:
            logger.error(f"Failed to fetch House trades: {e}")
            return []
        
    async def get_all_trades(self, limit_per_chamber: int = 50) -> List[TradeData]:
        logger.info(f"Fetching all congressional trades ({limit_per_chamber} per chamber)")
    
        senate_task = self.get_senate_trades(limit_per_chamber)
        house_task = self.get_house_trades(limit_per_chamber)  

        senate_trades, house_trades = await asyncio.gather(  
            senate_task, house_task, return_exceptions=True)
    
        all_trades = []
    
        if isinstance(senate_trades, list) and senate_trades:
            all_trades.extend(senate_trades)
        elif not isinstance(senate_trades, list):
            logger.error(f"Senate trades failed: {senate_trades}")

        if isinstance(house_trades, list) and house_trades:
            all_trades.extend(house_trades)
        elif not isinstance(house_trades, list):
            logger.error(f"House trades failed: {house_trades}")

        if not all_trades:
            logger.info("No real trades available - using mock data for testing")
            from datetime import datetime

            mock_trade1 = TradeData(
            politician_name="Nancy Pelosi",
            chamber="House",
            ticker="AAPL", 
            trade_type="Buy",
            amount=15000,
            transaction_date=datetime(2025, 1, 15),
            disclosure_date=datetime(2025, 2, 1)
            )

            mock_trade2 = TradeData(
            politician_name="Chuck Schumer",
            chamber="Senate", 
            ticker="MSFT",
            trade_type="Sell",
            amount=32500,
            transaction_date=datetime(2025, 1, 20),
            disclosure_date=datetime(2025, 2, 5)
            )

            all_trades = [mock_trade1, mock_trade2]

        if all_trades and hasattr(all_trades[0], 'transaction_date'):
            all_trades.sort(key=lambda x: x.transaction_date, reverse=True)

        logger.info(f"✅ Total trades fetched: {len(all_trades)}")
        return all_trades
    
    def _transform_trade_data(self, raw_data: dict, chamber: str)-> Optional[TradeData]:
        try:
            politician_name = raw_data.get("representative", "")
            politician_name = politician_name.replace("Hon. ", "").strip()
            if not politician_name:
                logger.warning("No politician name in trade data")

                return None

            ticker = raw_data.get("ticker", "").upper().strip()
            if not ticker or len(ticker)> 10:
                logger.warning(f"Invalid ticker:{ticker}")
                return None
            
            transaction = raw_data.get("transaction", "").lower()
            if "purchase" in transaction or "buy" in transaction:
                trade_type = "Buy"
            elif "sale" in transaction or "sell" in transaction:
                trade_type = "Sell"
            else:
                trade_type = transaction.title()
            
            amount_str = raw_data.get("amount", "")
            amount = self._parse_amount_range(amount_str)

            transaction_date = self._parse_date(raw_data.get("transactionDate"))
            disclosure_date = self._parse_date(raw_data.get("publicationDate"))

            if not transaction_date or not disclosure_date:
                logger.warning("Missing required dates in trade data")
                return None

            trade = TradeData(
                politician_name=politician_name,
                chamber=chamber,
                ticker=ticker,
                trade_type=trade_type,
                amount=amount,
                transaction_date=transaction_date,
                disclosure_date = disclosure_date
            )
            return trade
        except Exception as e:
            logger.error(f"Failed to transform trade data: {e}")
            return None
    def _parse_amount_range(self, amount_str: str) -> float:
        try:
            if not amount_str:
                return 0.0
            
            clean_str = amount_str.replace("$", "").replace(",", "")

            if " - " in clean_str:
                parts = clean_str.split(" - ")
                if len(parts) == 2:
                    min_amount = float(parts[0])
                    max_amount = float(parts[1])
                    return (min_amount + max_amount)/2
            
            return float(clean_str)
        
        except Exception:
            logger.warning(f"Could not parse amount: {amount_str}")
            return 0.0
        
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        try:
            if not date_str:
                return None
            
            return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            logger.warning(f"Could not parse date: {date_str}")
            return None
        