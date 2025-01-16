from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

user_device = Table(
    'user_devices',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('device_id', Integer, ForeignKey('devices.id'))
)

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, unique=True, index=True)
    name = Column(String)
    type = Column(String)
    last_seen = Column(DateTime(timezone=True))
    metadata = Column(JSON)
    users = relationship("User", secondary=user_device, back_populates="devices")

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    user = relationship("User", back_populates="voice_profiles")

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    patterns = Column(JSON)
    response_template = Column(String)
    variables = Column(JSON)
    category = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="templates")

# Update User model with relationships
User.voice_profiles = relationship("VoiceProfile", back_populates="user")
User.templates = relationship("Template", back_populates="user")
User.devices = relationship("Device", secondary=user_device, back_populates="users")
