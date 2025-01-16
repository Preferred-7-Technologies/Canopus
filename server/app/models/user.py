from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
from passlib.hash import bcrypt
from typing import List

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    voice_preference_id = Column(String, ForeignKey("voices.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    voice_preference = relationship("Voice", back_populates="users")
    tasks = relationship("Task", back_populates="user")
    devices = relationship("Device", back_populates="user")
    voice_commands = relationship("VoiceCommand", back_populates="user")
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.hashed_password = bcrypt.hash(password)

    def verify_password(self, password):
        return bcrypt.verify(password, self.hashed_password)
