from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from ..config import settings
from ..core.logging import setup_logging

logger = setup_logging()

class TaskScheduler:
    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
        }
        
        executors = {
            'default': ThreadPoolExecutor(20),
            'processpool': ProcessPoolExecutor(5)
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 3,
            'misfire_grace_time': 30
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )

    async def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Task scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start task scheduler: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Task scheduler shutdown successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown task scheduler: {str(e)}")
            raise

    async def add_job(self, func, trigger, **kwargs):
        """Add a new job to the scheduler"""
        try:
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                **kwargs
            )
            logger.info(f"Added new job: {job.id}")
            return job.id
        except Exception as e:
            logger.error(f"Failed to add job: {str(e)}")
            raise

scheduler = TaskScheduler()
