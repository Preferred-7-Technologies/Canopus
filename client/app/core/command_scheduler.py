from datetime import datetime, timedelta
import asyncio
from typing import Dict, Optional, List
import logging
from croniter import croniter
from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, DateTime, JSON
from .database import Base
import json

logger = logging.getLogger(__name__)

@dataclass
class ScheduledCommand:
    command: str
    schedule: str  # Cron expression or ISO timestamp
    recurring: bool
    metadata: Dict
    next_run: datetime

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True)
    command = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    recurring = Column(Boolean, default=False)
    metadata = Column(JSON)
    next_run = Column(DateTime, nullable=False)
    last_run = Column(DateTime, nullable=True)

class CommandScheduler:
    def __init__(self, db, command_processor):
        self.db = db
        self.command_processor = command_processor
        self.running = False
        self.tasks: Dict[int, asyncio.Task] = {}

    async def start(self):
        self.running = True
        await self._load_scheduled_tasks()
        asyncio.create_task(self._scheduler_loop())
        logger.info("Command scheduler started")

    async def stop(self):
        self.running = False
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        logger.info("Command scheduler stopped")

    async def schedule_command(self, command: str, schedule: str, 
                             recurring: bool = False, metadata: Dict = None) -> int:
        try:
            next_run = self._calculate_next_run(schedule)
            if not next_run:
                raise ValueError(f"Invalid schedule format: {schedule}")

            with self.db.get_session() as session:
                task = ScheduledTask(
                    command=command,
                    schedule=schedule,
                    recurring=recurring,
                    metadata=metadata or {},
                    next_run=next_run
                )
                session.add(task)
                session.commit()
                task_id = task.id

            await self._schedule_task(task_id, command, schedule, recurring, next_run)
            return task_id

        except Exception as e:
            logger.error(f"Failed to schedule command: {str(e)}")
            raise

    def _calculate_next_run(self, schedule: str) -> Optional[datetime]:
        try:
            # Try parsing as ISO timestamp
            return datetime.fromisoformat(schedule)
        except ValueError:
            # Try parsing as cron expression
            if croniter.is_valid(schedule):
                return croniter(schedule, datetime.now()).get_next(datetime)
        return None

    async def _scheduler_loop(self):
        while self.running:
            try:
                now = datetime.now()
                with self.db.get_session() as session:
                    due_tasks = session.query(ScheduledTask).filter(
                        ScheduledTask.next_run <= now
                    ).all()

                    for task in due_tasks:
                        await self._execute_task(task)
                        if task.recurring:
                            task.next_run = self._calculate_next_run(task.schedule)
                        else:
                            session.delete(task)
                    
                    session.commit()

                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler loop error: {str(e)}")
                await asyncio.sleep(60)

    async def _execute_task(self, task: ScheduledTask):
        try:
            await self.command_processor(task.command, task.metadata)
            task.last_run = datetime.now()
            logger.info(f"Executed scheduled task {task.id}: {task.command}")
        except Exception as e:
            logger.error(f"Failed to execute task {task.id}: {str(e)}")
