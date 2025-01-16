
from fastapi import APIRouter, Depends, HTTPException
from ....services.task_queue import TaskQueueService
from ....core.security import verify_api_key
from typing import Dict, Any

router = APIRouter()
task_service = TaskQueueService()

@router.post("/submit")
async def submit_task(
    task_data: Dict[str, Any],
    api_key: bool = Depends(verify_api_key)
):
    try:
        task_id = await task_service.submit_task(
            task_data["task_name"],
            args=task_data.get("args"),
            kwargs=task_data.get("kwargs")
        )
        return {"task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    api_key: bool = Depends(verify_api_key)
):
    try:
        status = await task_service.get_task_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))