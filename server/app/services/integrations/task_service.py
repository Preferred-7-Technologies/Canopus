from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...database import get_db
from ...models.task import Task
from ...core.logging import setup_logging

logger = setup_logging()

class TaskService:
    def __init__(self):
        self.db = next(get_db())

    async def manage_task(
        self, 
        action: str, 
        task_data: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if action == "create":
                return await self._create_task(task_data)
            elif action == "update":
                return await self._update_task(task_id, task_data)
            elif action == "delete":
                return await self._delete_task(task_id)
            elif action == "list":
                return await self._list_tasks()
            
            raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Task management failed: {str(e)}")
            raise

    async def _create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task = Task(
            title=task_data["title"],
            description=task_data.get("description"),
            due_date=datetime.fromisoformat(task_data["due_date"]),
            priority=task_data.get("priority", "medium")
        )
        self.db.add(task)
        self.db.commit()
        return {"status": "success", "task_id": task.id}

    async def _update_task(
        self, 
        task_id: str, 
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        for key, value in task_data.items():
            setattr(task, key, value)

        self.db.commit()
        return {"status": "success", "task_id": task_id}

    async def _delete_task(self, task_id: str) -> Dict[str, Any]:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        self.db.delete(task)
        self.db.commit()
        return {"status": "success", "task_id": task_id}

    async def _list_tasks(self) -> Dict[str, Any]:
        tasks = self.db.query(Task).all()
        return {
            "status": "success",
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "due_date": task.due_date.isoformat(),
                    "priority": task.priority,
                    "status": task.status
                }
                for task in tasks
            ]
        }
