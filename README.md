# Congressional Trading Analytics API 📊

A comprehensive FastAPI-based backend service for tracking and analyzing congressional stock trades with real-time data integration, authentication, and background processing capabilities.

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![Tests](https://img.shields.io/badge/Tests-100%25%20Pass-brightgreen.svg)

## 🚀 Features

### Core Functionality
- **📈 Real-time Congressional Trade Tracking** - Integration with Financial Modeling Prep API
- **🔐 JWT Authentication System** - Secure user registration, login, and protected routes
- **📊 Advanced Analytics** - Trade performance analysis, politician rankings, and insights
- **⚡ Background Job Processing** - Automated data synchronization with Celery
- **🔍 Comprehensive Search & Filtering** - By politician, ticker, date range, trade type
- **📱 RESTful API Design** - Clean, documented endpoints with OpenAPI/Swagger

### Technical Excellence
- **🧪 100% Test Coverage** - Comprehensive test suite with pytest
- **🐳 Docker Containerization** - Multi-service deployment ready
- **⚡ High Performance** - Async operations with SQLAlchemy 2.0
- **🔒 Security Best Practices** - Password hashing, input validation, CORS protection
- **📖 Auto-Generated Documentation** - Interactive API docs at `/docs`

## 🛠️ Tech Stack

**Backend Framework:** FastAPI + Uvicorn  
**Database:** PostgreSQL with SQLAlchemy ORM  
**Authentication:** JWT tokens with bcrypt password hashing  
**Background Jobs:** Celery with Redis broker  
**External API:** Financial Modeling Prep (FMP) integration  
**Testing:** pytest with 100% pass rate  
**Containerization:** Docker + docker-compose  
**Code Quality:** Type hints, async/await, comprehensive error handling  

## 🚦 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/congressional-trading-backend.git
cd congressional-trading-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Run migrations
alembic upgrade head

# Start the application
python -m app.main
```

### 3. Docker Deployment (Recommended)
```bash
# Copy and configure environment file for Docker
cp .env.docker.example .env.docker
# Edit .env.docker and add your real FMP API key

# Start all services
docker-compose up --build

# API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

## 📚 API Documentation

### Authentication Endpoints
```http
POST /auth/register     # User registration
POST /auth/login        # User authentication
GET  /auth/me           # Current user profile
```

### Trading Data Endpoints
```http
GET  /api/trades                    # List all trades (with filters)
GET  /api/trades?politician=Pelosi  # Filter by politician
GET  /api/trades?ticker=AAPL        # Filter by stock ticker
GET  /api/politicians               # List all politicians
GET  /api/politicians/{id}/trades   # Specific politician's trades
```

### Analytics Endpoints
```http
GET  /api/analytics/summary         # Trading summary statistics
GET  /admin/system-status          # System health (protected)
POST /admin/sync-trades            # Manual data sync (protected)
```

### Example API Calls
```bash
# Register new user
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "secure123", "full_name": "John Doe"}'

# Login and get JWT token
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "secure123"}'

# Get recent trades
curl "http://localhost:8000/api/trades?limit=10"

# Filter trades by politician
curl "http://localhost:8000/api/trades?politician=Nancy%20Pelosi"
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_api.py -v           # API endpoint tests
pytest tests/test_services.py -v     # Business logic tests
```

**Test Coverage:** 100% pass rate across authentication, API endpoints, database operations, and business logic.

## 🏗️ Architecture

### Directory Structure
```
congressional-trading-backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── auth.py              # JWT authentication system
│   ├── models.py            # SQLAlchemy database models
│   ├── services.py          # Business logic layer
│   ├── tasks.py             # Celery background jobs
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection setup
│   └── fmp_client.py        # Financial Modeling Prep API client
├── tests/                   # Comprehensive test suite
├── docker-compose.yml       # Multi-service Docker setup
├── Dockerfile              # Application containerization
└── requirements.txt        # Python dependencies
```

### Data Flow
```
FMP API → Background Jobs → PostgreSQL → FastAPI → Client Applications
    ↓           ↑               ↓           ↑
   Redis ← → Celery        Analytics ← → Authentication
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Security
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters
DEBUG=false

# External APIs (Required)
FMP_API_KEY=your-financial-modeling-prep-api-key

# Background Jobs
REDIS_URL=redis://localhost:6379/0

# Application
PROJECT_NAME=Congressional Trading API
ENVIRONMENT=production
ALLOWED_ORIGINS=["https://yourdomain.com"]
```

**Getting FMP API Key:**
1. Sign up at [Financial Modeling Prep](https://financialmodelingprep.com/)
2. Get your free API key from the dashboard
3. Add it to your `.env` or `.env.docker` file

### Database Schema
- **Users:** Authentication and user management
- **Politicians:** Congressional member profiles and statistics
- **Trades:** Individual stock transactions with full metadata
- **Optimized indexes** for common query patterns

## 🚀 Deployment

### Docker Production Deployment
```bash
# Production docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl http://localhost:8000/health
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start with Gunicorn (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000

# Start background worker
celery -A app.tasks worker --loglevel=info

# Start scheduler
celery -A app.tasks beat --loglevel=info
```

## 📈 Performance Features

- **Async Operations:** All I/O operations use async/await for maximum performance
- **Database Optimization:** Strategic indexes and query optimization
- **Caching Layer:** Redis caching for frequently accessed data
- **Connection Pooling:** Efficient database connection management
- **Background Processing:** Non-blocking data synchronization

## 🔒 Security Features

- **JWT Authentication:** Secure token-based authentication
- **Password Security:** bcrypt hashing with salt
- **Input Validation:** Pydantic models for request/response validation
- **CORS Protection:** Configurable cross-origin request handling
- **Rate Limiting:** API endpoint protection (configurable)
- **SQL Injection Prevention:** SQLAlchemy ORM protection

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Financial Modeling Prep** for providing congressional trading data API
- **FastAPI** for the excellent async web framework
- **SQLAlchemy** for robust ORM capabilities
- **pytest** for comprehensive testing framework

---
  
**💼 LinkedIn:** [LinkedIn](https://linkedin.com/in/maxwell-astafyev)

---
