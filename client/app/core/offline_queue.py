from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from .database import Base, LocalDatabase
from datetime import datetime
import json
import logging
from typing import List

logger = logging.getLogger(__name__)

class OfflineCommand(Base):
    __tablename__ = "offline_commands"
    id = Column(Integer, primary_key=True)
    command_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    synced = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)

class OfflineQueue:
    def __init__(self, db: LocalDatabase):
        self.db = db
        self.max_retries = 3

    async def enqueue(self, command_data: dict):
        try:
            with self.db.get_session() as session:
                offline_command = OfflineCommand(
                    command_data=command_data
                )
                session.add(offline_command)
                logger.info(f"Command queued for offline processing: {command_data}")
        except Exception as e:
            logger.error(f"Failed to enqueue command: {str(e)}")
            raise

    async def process_queue(self, api_client) -> List[dict]:
        results = []
        try:
            with self.db.get_session() as session:
                pending_commands = session.query(OfflineCommand).filter_by(
                    synced=False
                ).filter(
                    OfflineCommand.retry_count < self.max_retries
                ).all()

                for command in pending_commands:
                    try:
                        response = await api_client._make_request(
                            'POST',
                            'voice/process',
                            json=command.command_data
                        )
                        command.synced = True
                        results.append(response)
                    except Exception as e:
                        command.retry_count += 1
                        logger.error(f"Failed to process command {command.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process offline queue: {str(e)}")
            
        return results
