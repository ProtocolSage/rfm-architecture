"""
Database schema for RFM-Architecture.

This module defines the database models for:
- Users: Authentication and user management
- Presets: Fractal and visualization configurations
- ProgressRecords: Track and resume long-running operations
- PerformanceMetrics: Store benchmark and performance data
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """User model for authentication and profile management."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    presets = relationship("Preset", back_populates="user")
    performance_metrics = relationship("PerformanceMetric", back_populates="user")
    progress_records = relationship("ProgressRecord", back_populates="user")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Preset(Base):
    """Fractal preset configuration storage."""
    __tablename__ = 'presets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    fractal_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False)  # Store fractal parameters as JSON
    thumbnail = Column(LargeBinary, nullable=True)  # Optional thumbnail image
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    user = relationship("User", back_populates="presets")
    animation_keyframes = relationship("AnimationKeyframe", back_populates="preset")
    
    def __repr__(self):
        return f"<Preset(name='{self.name}', fractal_type='{self.fractal_type}')>"


class AnimationKeyframe(Base):
    """Animation keyframe storage for sequencing animations."""
    __tablename__ = 'animation_keyframes'
    
    id = Column(Integer, primary_key=True)
    sequence_name = Column(String(100), nullable=False)
    time_position = Column(Float, nullable=False)  # Position in seconds
    parameters = Column(JSON, nullable=False)  # Parameter state at this keyframe
    interpolation_type = Column(String(20), default="linear")  # linear, ease-in, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    preset_id = Column(Integer, ForeignKey('presets.id'))
    
    # Relationships
    preset = relationship("Preset", back_populates="animation_keyframes")
    
    def __repr__(self):
        return f"<AnimationKeyframe(sequence='{self.sequence_name}', time={self.time_position})>"


class ProgressRecord(Base):
    """Progress tracking for long-running operations."""
    __tablename__ = 'progress_records'
    
    id = Column(Integer, primary_key=True)
    operation_type = Column(String(50), nullable=False)  # render, animation, etc.
    status = Column(String(20), nullable=False)  # pending, in_progress, completed, failed
    progress_percent = Column(Float, default=0.0)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, nullable=True)
    message = Column(String(255), nullable=True)
    error_details = Column(Text, nullable=True)
    operation_data = Column(JSON, nullable=True)  # Additional operation-specific data
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    user = relationship("User", back_populates="progress_records")
    
    def __repr__(self):
        return f"<ProgressRecord(type='{self.operation_type}', progress={self.progress_percent}%)>"


class PerformanceMetric(Base):
    """Store performance benchmarks and monitoring data."""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_type = Column(String(50), nullable=False)  # render_time, memory_usage, fps
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # ms, MB, fps, etc.
    context = Column(JSON, nullable=True)  # Additional context (hardware, settings)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="performance_metrics")
    
    def __repr__(self):
        return f"<PerformanceMetric(type='{self.metric_type}', value={self.value} {self.unit})>"