from typing import Dict, Any, Optional
import logging
from celery import Celery
from ...config import settings
from ...models.task import TaskModel
from sqlalchemy.orm import Session
from ...database import get_db
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

class TaskManager:
    def __init__(self):
        self.celery = celery_app
        self.db = next(get_db())

    async def create_task(
        self,
        type: str,
        parameters: Dict[str, Any],
        user_id: str,
        priority: str = "normal"
    ) -> str:
        """Create a new background task"""
        try:
            task_id = str(uuid.uuid4())
            
            # Create task record
            db_task = TaskModel(
                id=task_id,
                type=type,
                parameters=parameters,
                user_id=user_id,
                priority=priority,
                status="pending"
            )
            self.db.add(db_task)
            self.db.commit()

            # Send to Celery
            celery_task = self.celery.send_task(
                f"tasks.{type}",
                args=[parameters],
                task_id=task_id,
                priority=self._get_priority_value(priority)
            )

            return task_id

        except Exception as e:
            logger.error(f"Task creation failed: {str(e)}")
            self.db.rollback()
            raise

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current status of a task"""
        try:
            task = self.db.query(TaskModel).filter(
                TaskModel.id == task_id
            ).first()
            
            if not task:
                return {"status": "not_found"}

            # Get Celery task status
            celery_task = self.celery.AsyncResult(task_id)
            
            return {
                "id": task.id,
                "type": task.type,
                "status": celery_task.status,
                "result": celery_task.result if celery_task.ready() else None,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            }

        except Exception as e:
            logger.error(f"Failed to get task status: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_priority_value(self, priority: str) -> int:
        """Convert priority string to Celery priority value"""
        priorities = {
            "high": 0,
            "normal": 5,
            "low": 9
        }
        return priorities.get(priority.lower(), 5)

    async def cleanup_tasks(self, max_age_days: int = 7):
        """Clean up old completed tasks"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            self.db.query(TaskModel).filter(
                TaskModel.created_at < cutoff_date,
                TaskModel.status.in_(["completed", "failed"])
            ).delete()
            self.db.commit()
        except Exception as e:
            logger.error(f"Task cleanup failed: {str(e)}")
            self.db.rollback()
