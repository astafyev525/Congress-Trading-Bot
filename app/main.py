from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
import time
import logging
from app.database import engine, get_db
from sqlalchemy.orm import Session
from app.models import Base, Trade, Politician, User
from app.config import get_settings
from app.auth import (
    UserCreate, UserLogin, Token, UserResponse,
    authenticate_user, create_user, create_access_token,
    get_current_user, get_current_active_user
)
from app.trading_endpoints import router as trading_router

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    logger.info(f"FMP API: {'Configured' if settings.FMP_API_KEY else 'Not configured'}")

    Base.metadata.create_all(bind = engine)
    logger.info(f"Database tables ready")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}")

app = FastAPI(
    title = settings.PROJECT_NAME,

    description="""
    Congressional Trading Analytics API

    Track and analyze stock trades with real-time data

    ##Features
    Real-time trade data from house and senate
    Politician profiles with performance metrics
    Advnanced filtering by date, amount, ticker, politician
    Analytics including performance calculations
    """,


    version = settings.VERSION,

    docs_url = "/docs",

    redoc_url = "/redoc",

    lifespan = lifespan
)

app.include_router(trading_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.ALLOWED_ORIGINS,

    allow_credentials = True,

    allow_methods = ["*"],

    allow_headers = ["*"]
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(f"{request.method} {request.url.path} - Started")

    response = await call_next(request)

    process_time = time.time() - start_time

    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f} s)")

    response.headers["X-Process-Time"] = str(process_time)

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc : Exception):
    logger.error(f"Error on {request.method} {request.url.path}: {str(exc)}")

    return JSONResponse(
        status_code = 500,
        content = {
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path)
        }
    )

@app.get("/", tags = ["Health"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "documentation":{
            "interactive_docs": "/docs",
            "redoc": "/redoc"
        },
        "endpoints":{
            "health": "/health",
            "trades": "/api/trades",
            "politicians": "/api/politicians",
            "analytics": "/api/analytics/summary",
            "auth_user": "/auth/register",
            "auth_login": "/auth/login",
            "auth_me": "/auth/me",
            "admin_sync": "/admin/sync-trades",        
            "admin_status": "/admin/system-status"  
        }

    }
        
@app.get("/health", tags = ["Health"])
async def health_check(db: Session = Depends(get_db)):
    try:
        politician_count = db.query(Politician).count()
        trade_count = db.query(Trade).count()
        user_count = db.query(User).count()

        start_time = time.time()
        db.query(Trade).first()
        db_response_time = time.time() - start_time

        return{
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api":{
                "name": settings.PROJECT_NAME,
                "version":settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "debug_mode": settings.DEBUG
            },
            "database":{
                "status": "connected",
                "url": settings.DATABASE_URL[:30] + "...",
                "response_time_ms": round(db_response_time * 1000, 2),
                "record_counts":{
                    "politicians": politician_count,
                    "trades": trade_count,
                    "users": user_count
                }
            },
            "configuration":{
                "fmp_api_configured": bool(settings.FMP_API_KEY),
                "jwt_secret_configured": bool(settings.JWT_SECRET_KEY),
                "cors_origins": len(settings.ALLOWED_ORIGINS)
            },
            "features":{
                "authentication": True,
                "caching": True,
                "rate_limiting": True,
                "background_sync": True
            }
        }
    except Exception as e:
        logger.error(f"Health check failed {str(e)}")
        return JSONResponse(
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            content = {
                "status":"unhealthy",
                "timestamp":datetime.now(timezone.utc).isoformat(),
                "api":{
                    "name":settings.PROJECT_NAME,
                    "version":settings.VERSION,
                    "environment":settings.ENVIRONMENT
                },
                "error":str(e),
                "database":{
                    "status":"error"
                }
            }
        )

@app.get("/api/trades", tags=["Trades"])
async def get_trades(
    limit:int = 50,
    offset:int = 0,
    politician:str = None,
    ticker:str = None,
    trade_type:str = None,
    db: Session = Depends(get_db)
):
    try:
        if limit >100:
            limit = 100
        if limit <1:
            limit = 1

        query = db.query(Trade)

        if politician:
            query = query.filter(Trade.politician_name.ilike(f"%{politician}%"))
        if ticker:
            query = query.filter(Trade.ticker.ilike(f"%{ticker}%"))
        if trade_type:
            query = query.filter(Trade.trade_type.ilike(f"%{trade_type}%"))

        query = query.order_by(Trade.transaction_date.desc())

        total_count = query.count()

        trades = query.offset(offset).limit(limit).all()

        trades_data = [trade.to_dict() for trade in trades]

        return{
            "trades":trades_data,
            "pagination":{
                "total":total_count,
                "limit":limit,
                "offset":offset,
                "has_more":offset+limit < total_count
            },
            "filters":{
                "politician":politician,
                "ticker":ticker,
                "trade_type":trade_type
            },
            "api_info":{
                "name":settings.PROJECT_NAME,
                "version":settings.VERSION
            },
            "timestamp":datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error gettings trades: {str(e)}")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Failed to retrieve trades"
        )

@app.get("/api/politicians", tags = ["Politicians"])
async def get_politicians(
    limit: int = 50,
    offset: int = 0,
    chamber: str = None,
    party: str = None,
    state: str = None,
    db: Session = Depends(get_db)
):
    try:
        if limit >50:
            limit = 50  
        if limit <1:
            limit = 1
        
        query = db.query(Politician)

        if chamber:
            query = query.filter(Politician.chamber.ilike(f"%{chamber}%"))
        if party:
            query = query.filter(Politician.party.ilike(f"%{party}%"))
        if state:
            query = query.filter(Politician.state.ilike(f"%{state}%"))
        
        query = query.order_by(Politician.name)

        total_count = query.count()
        politicians = query.offset(offset).limit(limit).all()

        politician_data = [politician.to_dict() for politician in politicians]

        return {
            "politicians":politician_data,
            "pagination":{
                "total":total_count,
                "limit":limit,
                "offset":offset,
                "has_more":offset+ limit <total_count
            },
            "filters": {
                "chamber": chamber,
                "party": party,
                "state": state
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting politicians: {str(e)}")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Failed to retrieve politicians"
        )
    
@app.get("/api/politicians/{politician_id}/trades",
tags = ["Politicians"])
async def get_politician_trades(
    politician_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    try:
        politician = db.query(Politician).filter(Politician.id == politician_id).first()
        if not politician:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "Politician not found"
            )
        
        query = db.query(Trade).filter(Trade.politician_name == politician.name)
        query = query.order_by(Trade.transaction_date.desc())

        total_count = query.count()
        trades = query.offset(offset).limit(limit).all()

        trades_data = [trade.to_dict() for trade in trades]

        return {
            "politician": politician.to_dict(),
            "trades": trades_data,
            "pagination":{
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting politician trades : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Failed to recieve politician trades"
        )

@app.get("/api/analytics/summary", tags = ["Analytics"])
async def get_analytics_summary(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import func
        
        total_politicians = db.query(Politician).count()
        total_trades = db.query(Trade).count()

        trade_stats = db.query(
            func.sum(Trade.estimated_amount).label('total_volume'),
            func.avg(Trade.estimated_amount).label('avg_trade_size'),
            func.max(Trade.estimated_amount).label('max_trade'),
            func.min(Trade.estimated_amount).label('min_trade')
            ).first()
        
        party_breakdown = db.query(
            Trade.party,
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.estimated_amount).label('total_volume')    
        ).group_by(Trade.party).all()

        top_traders = db.query(
            Trade.politician_name,
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.estimated_amount).label('total_volume')
        ).group_by(Trade.politician_name).order_by(func.sum(Trade.estimated_amount).desc()).limit(10).all()

        return {
            "summary":{
                "total_politicians": total_politicians,
                "total_trades": total_trades,
                "total_volume": float(trade_stats.total_volume or 0),
                "average_trade_size":float(trade_stats.avg_trade_size or 0),
                "largest_trade":float(trade_stats.max_trade or 0),
                "smallest_trade":float(trade_stats.min_trade or 0)
            },
            "party_breakdown":[
                {
                    "party": party,
                    "trade_count": trade_count,
                    "total_volume": float(total_volume or 0)
                }
                for party, trade_count, total_volume in party_breakdown
            ],
            "top_traders":[
                {
                    "politician": politician,
                    "trade_count": trade_count,
                    "total_volume": float(total_volume or 0)
                }
                for politician, trade_count, total_volume in top_traders
            ],
            "api_info":{
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT
            },
            "timestamp":datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting analytics {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Failed to retrieve analytics"
        )
@app.post("/auth/register", response_model = UserResponse, tags = ["Authentication"])
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(
            db = db,
            email = user_data.email,
            password = user_data.password,
            full_name = user_data.full_name
        )
        logger.info(f"New user registered {user.email}")

        return UserResponse(
            id = user.id,
            email = user.email,
            full_name = user.full_name,
            is_active = user.is_active,
            created_at = user.created_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Registration failed"
        )
    
@app.post("/auth/login", response_model = Token, tags = ["Authentication"])
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Incorrect email or password",
                headers = {"WWW-Authenticate": "Bearer"}
            )
        
        access_token = create_access_token(data = {"sub": user.email})
        logger.info(f"User logged in : {user.email}")

        return Token(
            access_token=access_token,
            token_type = "bearer"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "login failed"
        )
    
@app.get("/auth/me", response_model=UserResponse, tags = ["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return UserResponse(
        id = current_user.id,
        email = current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )

@app.get("/auth/protected", tags = ["Authentication"])
async def protected_example(current_user: User = Depends(get_current_active_user)):
    return {
        "message": f"Hello {current_user.email} This route provides authentication",
        "user_id":current_user.id,
        "email": current_user.email,
        "access_level": "authenticated",
        "timestamp":datetime.now(timezone.utc).isoformat()
    }
from app.auth import get_current_active_user
@app.post("/admin/sync-trades", tags = ["Admin"])
async def trigger_manual_sync(
    limit_per_chamber: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services import TradeService
        sync_result = TradeService.sync_trades_from_fmp(db, limit_per_chamber)

        background_task_id = None
        try:
            from app.tasks import manual_sync_task
            background_task = manual_sync_task.delay(limit_per_chamber)
            background_task_id = background_task.id
        except Exception as e:
            logger.warning(f"Could not queue background task: {e}")

        return{
            "message": "Trade sync completed",
            "direct_sync": sync_result,
            "background_task_id": background_task_id,
            "triggered_by": current_user.email,
            "timestamp": datetime.now(timezone.utc)
        }
    
    except Exception as e:
        logger.error(f"Manual sync failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Sync failed: {str(e)}"
        )
    
@app.get("/admin/task-status/{task_id}", tags = ["Admin"])
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        from app.tasks import celery_app
        result = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": result.status,
            "checked_by": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if result.status == "SUCCESS":
            response["result"] = result.result
        elif result.status == "FAILURE":
            response["error"] = str(result.info)
        elif result.status == "PENDING":
            response["message"] = "Task is queued or being processed"

        return response
    except Exception as e:
        logger.error(f"Task status check failed {str(e)}")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Could not check taks status : {str(e)}"
        )
    
@app.get("/admin/workers", tags = ["Admin"])
async def get_worker_status(current_user: User = Depends(get_current_active_user)):
    try:
        from app.tasks import celery_app
        inspector = celery_app.control.inspect()

        active_tasks = inspector.active() or {}
        registered_tasks = inspector.registered() or {}
        worker_stats = inspector.stats or {}

        return{
            "workers": {
                "active_tasks": active_tasks,
                "registered_tasks": list(registered_tasks.keys()) if registered_tasks else [],
                "worker_stats": worker_stats,
                "total_workers": len(worker_stats)
            },
            "celery_info": {
                "broker_url": str(celery_app.conf.broker_url),
                "result_backend": str(celery_app.conf.result_backend),
                "task_serializer": celery_app.conf.task_serializer
            },
            "checked_by": current_user.email,
            "timestamp": datetime.now(timezone.utc)
        }
    
    except Exception as e:
        logger.warning(f"Worker status check faild: {str(e)}")
        return {
            "error": f"Could not connect to celery: {str(e)}",
            "message": "Make sure Redis and Celery workers are running",
            "workers": {"total_workers": 0},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
@app.get("/admin/system-status", tags = ["Admin"])
async def get_system_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    status_info = {
        "checked_by": current_user.email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "celery": {"status": "unknown"},
        "recent_activity": {}
        }
    
    try:
        trade_count = db.query(Trade).count()
        politician_count = db.qeury(Politician).count()

        yesterday = datetime.now(timezone.utc) - timedelta(days = 1)
        recent_trades = db.query(Trade).filter(
            Trade.created_at >= yesterday
        ).count()

        status_info["databse"] = {
            "status": "connected",
            "total_trades": trade_count,
            "total_politicians": politician_count,
            "trades_added_today": recent_trades
        }
    
    except Exception as e:
        status_info["database"] = {
            "status": "error",
            "error": str(e)
        }

    try:
        import redis
        r = redis.Redis(host = 'localhost', port = 6379, db = 0)
        r.ping()
        status_info["redis"] = {
            "status": "connected",
            "host": "localhost:6379"
        }
    except Exception as e:
        status_info["redis"] = {
            "status": "error",
            "error": str(e)
        }

    try:
        from app.tasks import celery_app
        inspector = celery_app.control.inspect()
        worker_stats = inspector.stats() or {}

        status_info["celery"] = {
            "status": "connected" if worker_stats else "no_workers",
            "active_workers": len(worker_stats),
            "worker_names": list(worker_stats.keys())
        }
    except Exception as e:
        status_info["celery"] = {
            "status": "error",
            "error": str(e)
        }

    return status_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host = "0.0.0.0",
        port = 8000,
        reload = settings.DEBUG,
        log_level = "info"
    )     

