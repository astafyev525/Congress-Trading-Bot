from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging
from app.config import settings
from typing import Iterator


logger = logging.getLogger(__name__)

database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(
    database_url,
    echo = settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine
)

Base = declarative_base()

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db

    except Exception as e:
        db.rollback()
        logger.error(f"Database session error {e}")
        raise
    finally:
        db.close()


def create_tables():
    try:
        from app.models import Trade, Politician, User

        Base.metadata.create_all(bind = engine)
        logger.info("Database tables created successfully")
        return True

    except Exception as e:
        print(f"Failed to create tables {e}")
        logger.error(f"Failed to create database tabels {e}")
        return False

def test_connection():
    try:
        db = SessionLocal()
        result = db.execute(text("Select 1 as test_column"))
        test_value = result.fetchone()[0]
        db.close()

        if test_value ==1 :
            print("Connection Successful")
            logger.info("Connection successful")
            return True
        else:
            print("Connection failed")
            return False

    except Exception as e:
        print(f"Connection failed {e}")
        logger.error(f"Connection failed {e}")
        return False

def get_database_info():
    try:
        db = SessionLocal()

        result = db.execute(text("Select version()"))
        version = result.fetchone()[0]

        result = db.execute(text("Select current_database()"))
        db_name = result.fetchone()[0]

        db.close()

        return {
            "database_url": database_url,
            "database_name": db_name,
            "postgresql_version": version,
            "connection_pool_size": engine.pool.size(),
            "checked_in_connections": engine.pool.checkedin()
        }

    except Exception as e:
        logger.error(f"Failed to get database info {e}")
        return{"error": str(e)}

def close_database():
    try:
        engine.dispose()
        print("Connection closed")
        logger.info("Database connection closed")
    except Exception as e:
        print(f"Error closing connection {e}")
        logger.error(f"Error closing connection {e}")

def main():
    if not test_connection():
        print("Connection failed")
        return False
    
    info = get_database_info()
    for key,value in info.items():
        print(f" {key}: {value}")

    print("Everything works")
    return True

if __name__ == "__main__":
    main()
