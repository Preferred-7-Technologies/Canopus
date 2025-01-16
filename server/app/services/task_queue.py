
from celery import Celery
from ..config import settings
from typing import Any, Dict
import asyncio
from ..core.logging import setup_logging

logger = setup_logging()

class TaskQueueService:
    def __init__(self):
        self.celery = Celery(
            "Canopus",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND
        )
        self.task_routes = {
            'process_voice_command': {'queue': 'voice'},
            'process_ai_request': {'queue': 'ai'}
        }
        
    async def submit_task(
        self, 
        task_name: str, 
        args: tuple = None, 
        kwargs: Dict[str, Any] = None
    ) -> str:
        """Submit task to queue"""
        try:
            task = self.celery.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                queue=self.task_routes.get(task_name, {}).get('queue', 'default')
            )
            return task.id
        except Exception as e:
            logger.error(f"Task submission failed: {str(e)}")
            raise
            
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and result"""
        try:
            task = self.celery.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": task.status,
                "result": task.result if task.successful() else None,
                "error": str(task.result) if task.failed() else None
            }
        except Exception as e:
            logger.error(f"Failed to get task status: {str(e)}")
            raise