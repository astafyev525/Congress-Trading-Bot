import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from celery import Celery
from celery.schedules import crontab
from app.config import get_settings
from app.database import SessionLocal
from app.services import TradeService, PoliticianService

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

celery_app = Celery(
    "congressional-trading-tasks",
    broker = "redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

celery_app.conf.update(
    timezone = 'UTC',
    enable_utc = True,

    task_serializer = 'json',
    accept_content = ['json'],
    result_serializer = 'json',
    result_expires = 3600,

    worker_prefetch_multiplier = 1,
    task_acks_late = True,

    task_default_retry_delay = 60,
    task_max_retires = 3,
)

celery_app.conf.beat_schedule = {
    'synnc-trades-hourly': {
        'task': 'app.tasks.sync_trades_task',
        'schedule': crontab(minute = 0),
        'args': (50,)
    },

    'update-politician-stats-daily': {
        'task': 'app.tasks.update_politician_stats_task',
        'schedule': crontab(hour = 2, minute = 0)
    },

    'cleanup-logs-weekly': {
        'task': 'app.tasks.cleanup_task',
        'schedule': crontab(hour = 3, minute = 0, day_of_week= 0)
    }

}


@celery_app.task(bind = True, name = "app.tasks.sync_trades_task")
def sync_trades_task(self, limit_per_chamber: int = 100) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"Starting trade sync task {task_id} (limit: {limit_per_chamber})")
    db = SessionLocal()

    try:
        sync_result = TradeService.sync_trades_from_fmp(db, limit_per_chamber)

        sync_result.update({
            "task_id": task_id,
            "task_name": "sync_trades_task",
            "limit_per_chamber": limit_per_chamber
        })

        if sync_result["sucess"]:
            logger.info(
                f"trade sync task {task_id} completed successfully"
                f"{sync_result['trades_stored']} stored, {sync_result['trades_updated']} updated"
            )
        else:
            logger.error(f"Trade sync task {task_id} failed: {sync_result.get('errors', [])}")

        return sync_result
    except Exception as e:
        error_mgs = f"Trade sync task {task_id} failed with exception {str(e)}"
        logger.error(error_mgs)

        raise self.retry(exc = e, countdown = 60, max_retries = 3)
    
    finally:
        db.close()

@celery_app.task(bind = True, name = "app.tasks.update_politician_stats_task")
def update_politician_stats_task(self) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info(f"Starting politician stats update task {task_id}")

    db = SessionLocal()

    try:
        start_time = datetime.now(timezone.utc)

        TradeService._update_politician_stats(db)
        db.commit()

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        from app.models import Politician
        politician_count = db.query(Politician).count()
        result = {
            "task_id": task_id,
            "task_name": "update_poltician_stats_task",
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": duration,
            "politicians_updated": politician_count,
            "success": True
        }

        logger.info(f"Politician stats task {task_id} completed: {politician_count} politicians updated")

        return result
    except Exception as e:
        db.rollback()
        error_msg = f"Politician stats task{task_id} failed : {str(e)}"
        logger.error(error_msg)

        raise self.retry(exc = e, countdown = 60, max_retries = 3)
    
    finally:
        db.close()

@celery_app.task(bind = True, name = "app.tasks.cleanup_task")
def cleanup_task(self, days_to_keep: int = 90) -> Dict[str,Any]:
    task_id = self.request.id
    logger.info(f"Starting cleanup task {task_id} (keeping {days_to_keep} days)")

    try:
        start_time = datetime.now(timezone.utc)
        cutoff_date = start_time - timedelta(days = days_to_keep)

        cleanup_count = 0

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        result = {
            "task_id": task_id,
            "task_name": "cleanup_task",
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": duration,
            "days_to_keep": days_to_keep,
            "cutoff_date": cutoff_date.isoformat(),
            "items_cleaned": cleanup_count,
            "success": True
        }

        logger.info(f"Cleanup task {task_id} completed: {cleanup_count} items cleaned")
        return result

    except Exception as e:
        error_msg = f"Cleanup task {task_id} failed: {str(e)}"
        logger.error(error_msg)

        raise self.retry(exc = e, countdown = 60, max_retries = 3)

@celery_app.task(name = "app.tasks.manual_sync_task")
def manual_sync_task(limit_per_chamber: int = 20) -> str:
    logger.info(f"Manual sync task started (limit: {limit_per_chamber})")

    db = SessionLocal()

    try:
        result = TradeService.sync_trades_from_fmp(db, limit_per_chamber)

        if result["success"]:
            message = f"Maual sync completed {result['trades_stored']} new trades stored"
        else:
            message = f"Manual sync failed {result.get('errors', [])}"
        
        logger.info(message)
        return message
    except Exception as e:
        error_msg = f"Manual sync failed: {str(e)}"
        logger.error(error_msg)
        return error_msg

    finally:
        db.close()

def test_celery_connection():
    print("Testing celery connection")

    try:
        inspector = celery_app.control.inspect()
        stats = inspector.stats()

        if stats:
            print("Celery workers are running")
            for worker, worker_stats in stats.items():
                print(f"Worker: {worker}")
        else:
            print("No celery workers founds")
        
        print("Testing manual task")
        result = manual_sync_task.delay(limit_per_chamber = 2)

        print(f"Task qeued with ID: {result.id}")
        print("Start a worker to process is")

        return True
    except Exception as e:
        print(f"Celery test failed: {e}")
        return False

if __name__ == "__main__":
    test_celery_connection()

