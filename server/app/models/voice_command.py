from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class VoiceCommand(Base):
    __tablename__ = "voice_commands"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    command_text = Column(String, nullable=False)
    processed_text = Column(String)
    status = Column(String, nullable=False)  # pending, processing, completed, failed
    confidence_score = Column(Float)
    execution_time = Column(Float)  # in seconds
    response_data = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="voice_commands")
    actions = relationship("CommandAction", back_populates="voice_command")

class CommandAction(Base):
    __tablename__ = "command_actions"

    id = Column(Integer, primary_key=True)
    command_id = Column(Integer, ForeignKey("voice_commands.id"))
    action_type = Column(String, nullable=False)
    parameters = Column(JSON)
    status = Column(String, nullable=False)
    result = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True))

    # Relationships
    voice_command = relationship("VoiceCommand", back_populates="actions")
