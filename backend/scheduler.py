"""
APScheduler configuration for background jobs
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

# Configure job stores and executors
jobstores = {
    'default': MemoryJobStore()
}

executors = {
    'default': ThreadPoolExecutor(max_workers=5)
}

job_defaults = {
    'coalesce': True,  # Combine multiple pending executions into one
    'max_instances': 1,  # Only one instance of each job at a time
    'misfire_grace_time': 60  # Allow 60 seconds grace for late jobs
}

# Create scheduler instance
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC'
)


def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        try:
            # Import worker functions (avoid circular import)
            from workers.post_scheduler import check_scheduled_posts

            # Add scheduled post checker (runs every minute)
            scheduler.add_job(
                func=check_scheduled_posts,
                trigger=IntervalTrigger(minutes=1),
                id='check_scheduled_posts',
                name='Check and publish scheduled posts',
                replace_existing=True
            )

            scheduler.start()
            logger.info("✅ APScheduler started successfully")
            logger.info("📅 Scheduled post checker: Every 1 minute")

        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            raise
    else:
        logger.info("⚠️ Scheduler already running")


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 APScheduler stopped")


def get_scheduler_status():
    """Get current scheduler status and jobs"""
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in scheduler.get_jobs()
        ]
    }


# Export scheduler for direct access if needed
__all__ = ['scheduler', 'start_scheduler', 'stop_scheduler', 'get_scheduler_status']
