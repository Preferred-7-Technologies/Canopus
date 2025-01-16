import asyncio
from typing import Dict, Callable, Any, Optional
import logging
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class BackgroundService:
    def __init__(self, config):
        self.config = config
        self.tasks: Dict[str, asyncio.Task] = {}
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self._stats_file = Path("data/background_stats.json")
        self._load_stats()

    def _load_stats(self):
        try:
            if self._stats_file.exists():
                with open(self._stats_file, "r") as f:
                    self.stats = json.load(f)
            else:
                self.stats = {
                    "tasks_completed": 0,
                    "last_run": None,
                    "errors": 0
                }
        except Exception as e:
            logger.error(f"Failed to load background stats: {str(e)}")
            self.stats = {"tasks_completed": 0, "last_run": None, "errors": 0}

    async def start(self):
        if self.running:
            return
        
        self.running = True
        self.tasks["monitor"] = asyncio.create_task(self._monitor_tasks())
        logger.info("Background service started")

    async def stop(self):
        self.running = False
        for task in self.tasks.values():
            task.cancel()
        
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self._save_stats()
        logger.info("Background service stopped")

    def register_handler(self, event_type: str, handler: Callable):
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for {event_type}")

    async def process_task(self, task_type: str, data: Any) -> Optional[Any]:
        try:
            if task_type in self.handlers:
                task = asyncio.create_task(self.handlers[task_type](data))
                self.tasks[f"{task_type}_{datetime.now().timestamp()}"] = task
                result = await task
                self.stats["tasks_completed"] += 1
                return result
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Task processing failed: {str(e)}")
            return None

    async def _monitor_tasks(self):
        while self.running:
            try:
                # Clean up completed tasks
                completed_tasks = [
                    name for name, task in self.tasks.items()
                    if task.done() and name != "monitor"
                ]
                
                for task_name in completed_tasks:
                    task = self.tasks.pop(task_name)
                    try:
                        await task  # Handle any exceptions
                    except Exception as e:
                        logger.error(f"Task {task_name} failed: {str(e)}")
                
                self.stats["last_run"] = datetime.now().isoformat()
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task monitor error: {str(e)}")
                await asyncio.sleep(60)

    def _save_stats(self):
        try:
            with open(self._stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save background stats: {str(e)}")
