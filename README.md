# Congressional Trading Analytics + Trading Bot 🏛️📊

A **FastAPI-based congressional trading analytics platform** with a **basic automated trading bot** that can mirror congressional stock trades using Alpaca API integration.

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Alpaca](https://img.shields.io/badge/Alpaca-Trading-orange.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

## 🚀 What This System Does

### **Congressional Trading Analytics (Core Features)**
- **📊 Real-time Data**: Fetches congressional trades from Financial Modeling Prep API every hour
- **🔍 Advanced Filtering**: Search by politician, ticker, trade type, date ranges
- **📈 Performance Analytics**: Track politician trading statistics and insights  
- **🏛️ Comprehensive Database**: Normalized PostgreSQL schema with trade and politician data
- **🔐 Authentication**: JWT-based user management with secure registration/login

### **Basic Trading Bot (New Feature)**
- **🤖 Simple Copy Trading**: Automatically copies trades from politicians you follow
- **⚡ Automated Processing**: Checks for new congressional trades every 30 minutes
- **🛡️ Basic Risk Management**: Configurable trade size limits and politician filtering
- **📱 API Control**: Start/stop bot and view basic status via REST endpoints
- **🧪 Paper Trading**: Safe testing with Alpaca's paper trading environment

## 🏗️ Architecture

**Technology Stack:**
- **FastAPI + Uvicorn** - Async web framework with auto-generated docs
- **PostgreSQL** - Financial data storage  
- **Celery + Redis** - Background task processing and automation
- **Alpaca Trading API** - Stock trading execution (paper trading default)
- **Docker** - Containerized multi-service deployment

### **🔄 Data Flow Architecture**

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│                     │    │                      │    │                     │
│      Users          │◀───│     FastAPI          │◀───│   PostgreSQL        │
│   (Web/API          │    │   Web Server         │    │   Database          │
│   Requests)         │    │   + Auth System      │    │   (Trade Data)      │
│                     │    │                      │    │                     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                                                    ▲
                                                                    │
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│                     │    │                      │    │                     │
│   Financial         │───▶│   Celery Workers     │───▶│    Redis Task       │
│   Modeling Prep     │    │   (Background        │    │    Queue + Cache    │
│   (Congressional    │    │   Data Sync +        │    │                     │
│   Trade Data)       │    │   Trading Bot)       │    │                     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                      │                           ▲
                                      ▼                           │
┌─────────────────────┐    ┌──────────────────────┐              │
│                     │    │                      │              │
│   Alpaca Trading    │◀───│   Celery Beat        │──────────────┘
│   API               │    │   (Task Scheduler)   │
│   (Stock Execution) │    │   - Every 30min      │
│                     │    │   - Trade Processing │
└─────────────────────┘    └──────────────────────┘
```

**System Flow:**
1. **Celery Beat** schedules background tasks (hourly sync + 30min bot processing)
2. **Celery Workers** fetch new congressional trades from **FMP API**
3. **Workers** store normalized data in **PostgreSQL**
4. **Workers** process new trades for active trading bots
5. **Workers** execute trades via **Alpaca API** when conditions are met
6. **FastAPI** serves stored data and manages user requests
7. **Redis** manages task queues and caches API responses

## 📊 Available Endpoints

### **Congressional Data (Original Features)**
```http
GET  /                              # API info and available endpoints
GET  /health                        # System health check
GET  /api/trades                    # Browse congressional trades (with filters)
GET  /api/politicians               # List politicians with stats
GET  /api/politicians/{id}/trades   # Specific politician's trades  
GET  /api/analytics/summary         # Trading summary statistics
```

### **Authentication**
```http
POST /auth/register                 # Create new user account
POST /auth/login                    # Get JWT authentication token
GET  /auth/me                       # View current user profile
```

### **Trading Bot (New)**
```http
POST /api/trading/account/connect   # Connect your Alpaca account
POST /api/trading/bot/start         # Start the trading bot
GET  /api/trading/bot/status        # View bot status and basic stats
```

## 🚦 Quick Start

### **1. Get API Keys (Required)**
```bash
# Financial Modeling Prep (congressional data)
# Sign up at: https://financialmodelingprep.com/
FMP_API_KEY=your_fmp_api_key

# Alpaca (stock trading - paper trading is free)  
# Sign up at: https://alpaca.markets/
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
```

### **2. Environment Setup**
```bash
# Clone and setup
git clone [your-repo-url]
cd congressional-trading-backend

# Copy environment file
cp .env.example .env
# Add your API keys to .env file

# Option 1: Docker (Recommended)
docker-compose up --build

# Option 2: Manual setup  
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

### **3. Basic Usage**
```bash
# Register user account
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@email.com", "password": "secure123"}'

# Login to get token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@email.com", "password": "secure123"}'

# Connect Alpaca account
curl -X POST "http://localhost:8000/api/trading/account/connect" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"api_key": "YOUR_ALPACA_KEY", "secret_key": "YOUR_ALPACA_SECRET"}'

# Start trading bot
curl -X POST "http://localhost:8000/api/trading/bot/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🤖 How the Trading Bot Works

### **Current Implementation (Basic)**
1. **Data Collection**: System fetches new congressional trades every hour via FMP API
2. **Trade Processing**: Every 30 minutes, Celery task checks for unprocessed trades
3. **Filtering Logic**: 
   - Only copies trades from politicians you follow (default: Nancy Pelosi)
   - Only processes "Buy" orders (skips sells)
   - Minimum trade size: $15,000
4. **Position Sizing**: Your trade = 10% of politician's trade amount (max $1,000)
5. **Execution**: Places market order via Alpaca API in paper trading mode

### **Example Trading Flow**
```
Nancy Pelosi buys $50,000 of AAPL
↓
Bot processes within 30 minutes  
↓
Your account: Market buy $1,000 of AAPL (capped at max)
↓
Trade recorded in bot_trades table
```

### **Bot Status Response**
```json
{
  "is_active": true,
  "total_trades": 3,
  "total_pnl": 0.0,
  "followed_politicians": ["Nancy Pelosi"]
}
```

## 🛡️ Safety Features

**Built-in Risk Management:**
- ✅ **Paper Trading Default** - No real money at risk initially
- ✅ **Position Limits** - Max $1,000 per trade (configurable in settings)
- ✅ **Trade Filtering** - Only significant trades ($15k+) from followed politicians  
- ✅ **Authentication Required** - All bot endpoints require valid JWT tokens
- ✅ **Manual Control** - Start/stop bot anytime via API

## 🔧 Configuration Options

**Environment Variables:**
```bash
# Core settings
FMP_API_KEY=your_fmp_key
ALPACA_API_KEY=your_alpaca_key  
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_PAPER_TRADING=true           # Set false for live trading
ENABLE_TRADING_BOT=true             # Master enable/disable

# Security
JWT_SECRET_KEY=your-secure-key-32-chars-min
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 📋 Project Structure (Updated)

```
congressional-trading-backend/
├── app/
│   ├── main.py                     # FastAPI app + trading router
│   ├── models.py                   # Database models (+ 3 new trading tables)
│   ├── auth.py                     # JWT authentication
│   ├── fmp_client.py              # Congressional data fetching
│   ├── alpaca_client.py           # NEW: Alpaca trading integration
│   ├── trading_service.py         # NEW: Core trading logic  
│   ├── trading_endpoints.py       # NEW: Trading API routes
│   ├── trading_tasks.py           # NEW: Background automation
│   ├── services.py                # Congressional data processing
│   └── tasks.py                   # Celery task scheduling (+ trading task)
├── tests/                         # Test suite (original)
├── requirements.txt               # Dependencies (+ alpaca-py, pandas, numpy)
├── docker-compose.yml             # Multi-service deployment
└── README.md                      # This file
```

## 🧪 Testing

### **Test Your Setup**
```bash
# Test Alpaca connection
python -m app.alpaca_client

# Check API endpoints
curl http://localhost:8000/docs

# Monitor background tasks
celery -A app.tasks inspect active

# Run existing test suite
pytest tests/ -v
```

### **Verify Trading Bot**
```bash
# Check if bot is processing trades
curl "http://localhost:8000/api/trades?limit=5"

# Monitor bot status
curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/api/trading/bot/status"

# Check database for bot trades
# (Connect to PostgreSQL and query bot_trades table)
```

## ⚖️ Legal Disclaimer

**Important Notice:**
- 📚 **Educational Purpose**: This software is for learning and research
- ⚠️ **Not Financial Advice**: Trade at your own risk  
- 🧪 **Use Paper Trading**: Test thoroughly before considering live trading
- 🔒 **Secure Your Keys**: API credentials are your responsibility
- 📋 **Compliance**: Ensure compliance with local trading regulations

**Risk Warning:** Algorithmic trading involves substantial risk of loss. Past performance of politicians does not guarantee future results. Only invest money you can afford to lose.

## 🚀 Getting Started

1. **Set up the basic system** following the Quick Start guide
2. **Connect your Alpaca paper trading account**  
3. **Start the bot and monitor its behavior**
4. **Review trades in the bot_trades table**
5. **Consider enhancements based on your needs**

---

**⭐ Star this repo if you found it useful!**

*Built with FastAPI, PostgreSQL, and Alpaca for educational trading automation*