from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from typing import Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class VoiceCommand(Base):
    __tablename__ = "voice_commands"
    id = Column(Integer, primary_key=True)
    command_text = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # pending, completed, failed
    command_metadata = Column(JSON)  # Renamed from metadata to command_metadata

class LocalDatabase:
    def __init__(self, config):
        self.engine = create_engine(f"sqlite:///{config.LOCAL_DB_PATH}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        logger.info("Database initialized")

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()

    def save_command(self, command_text: str, status: str, metadata: dict = None):
        try:
            with self.get_session() as session:
                command = VoiceCommand(
                    command_text=command_text,
                    status=status,
                    command_metadata=metadata
                )
                session.add(command)
                logger.info(f"Saved command: {command_text}")
                return command
        except Exception as e:
            logger.error(f"Failed to save command: {str(e)}")
            raise

    def get_commands(self, limit: int = 100) -> list:
        try:
            with self.get_session() as session:
                return session.query(VoiceCommand)\
                    .order_by(VoiceCommand.timestamp.desc())\
                    .limit(limit)\
                    .all()
        except Exception as e:
            logger.error(f"Failed to get commands: {str(e)}")
            return []
