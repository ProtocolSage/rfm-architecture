"""
Database repository classes for RFM-Architecture.

This module provides repository classes for database operations.
Each repository is responsible for CRUD operations on a specific model.
"""
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, func

from rfm.database.connection import db_session
from rfm.database.schema import (
    User, Preset, AnimationKeyframe, ProgressRecord, PerformanceMetric
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common database operations."""
    
    def __init__(self, model_class):
        """
        Initialize repository with model class.
        
        Args:
            model_class: The SQLAlchemy model class
        """
        self.model_class = model_class
    
    def get_by_id(self, entity_id: int) -> Optional[Any]:
        """
        Get entity by ID.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            The entity or None if not found
        """
        with db_session() as session:
            return session.query(self.model_class).filter_by(id=entity_id).first()
    
    def get_all(self) -> List[Any]:
        """
        Get all entities.
        
        Returns:
            List of entities
        """
        with db_session() as session:
            return session.query(self.model_class).all()
    
    def create(self, data: Dict[str, Any]) -> Any:
        """
        Create a new entity.
        
        Args:
            data: Entity data dictionary
            
        Returns:
            The created entity
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        with db_session() as session:
            entity = self.model_class(**data)
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity
    
    def update(self, entity_id: int, data: Dict[str, Any]) -> Optional[Any]:
        """
        Update an entity.
        
        Args:
            entity_id: The entity ID
            data: Updated entity data dictionary
            
        Returns:
            The updated entity or None if not found
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        with db_session() as session:
            entity = session.query(self.model_class).filter_by(id=entity_id).first()
            if not entity:
                return None
            
            for key, value in data.items():
                setattr(entity, key, value)
            
            session.commit()
            session.refresh(entity)
            return entity
    
    def delete(self, entity_id: int) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        with db_session() as session:
            entity = session.query(self.model_class).filter_by(id=entity_id).first()
            if not entity:
                return False
            
            session.delete(entity)
            session.commit()
            return True


class UserRepository(BaseRepository):
    """Repository for User operations."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: The username
            
        Returns:
            The user or None if not found
        """
        with db_session() as session:
            return session.query(User).filter_by(username=username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: The email address
            
        Returns:
            The user or None if not found
        """
        with db_session() as session:
            return session.query(User).filter_by(email=email).first()
    
    def update_last_login(self, user_id: int) -> Optional[User]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: The user ID
            
        Returns:
            The updated user or None if not found
        """
        return self.update(user_id, {"last_login": datetime.utcnow()})


class PresetRepository(BaseRepository):
    """Repository for Preset operations."""
    
    def __init__(self):
        super().__init__(Preset)
    
    def get_by_user(self, user_id: int) -> List[Preset]:
        """
        Get presets by user ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of presets
        """
        with db_session() as session:
            return session.query(Preset).filter_by(user_id=user_id).all()
    
    def get_public_presets(self) -> List[Preset]:
        """
        Get all public presets.
        
        Returns:
            List of public presets
        """
        with db_session() as session:
            return session.query(Preset).filter_by(is_public=True).all()
    
    def search_presets(self, search_term: str, user_id: Optional[int] = None) -> List[Preset]:
        """
        Search presets by name or description.
        
        Args:
            search_term: The search term
            user_id: Optional user ID to filter by
            
        Returns:
            List of matching presets
        """
        with db_session() as session:
            query = session.query(Preset).filter(
                (Preset.name.ilike(f"%{search_term}%")) | 
                (Preset.description.ilike(f"%{search_term}%"))
            )
            
            if user_id:
                query = query.filter(
                    (Preset.user_id == user_id) | (Preset.is_public == True)
                )
            else:
                query = query.filter(Preset.is_public == True)
                
            return query.all()


class AnimationKeyframeRepository(BaseRepository):
    """Repository for AnimationKeyframe operations."""
    
    def __init__(self):
        super().__init__(AnimationKeyframe)
    
    def get_by_preset(self, preset_id: int) -> List[AnimationKeyframe]:
        """
        Get keyframes by preset ID.
        
        Args:
            preset_id: The preset ID
            
        Returns:
            List of keyframes ordered by time position
        """
        with db_session() as session:
            return session.query(AnimationKeyframe).filter_by(
                preset_id=preset_id
            ).order_by(AnimationKeyframe.time_position).all()
    
    def get_by_sequence(self, preset_id: int, sequence_name: str) -> List[AnimationKeyframe]:
        """
        Get keyframes by sequence name.
        
        Args:
            preset_id: The preset ID
            sequence_name: The sequence name
            
        Returns:
            List of keyframes in the sequence ordered by time position
        """
        with db_session() as session:
            return session.query(AnimationKeyframe).filter_by(
                preset_id=preset_id,
                sequence_name=sequence_name
            ).order_by(AnimationKeyframe.time_position).all()


class ProgressRecordRepository(BaseRepository):
    """Repository for ProgressRecord operations."""
    
    def __init__(self):
        super().__init__(ProgressRecord)
    
    def get_active_for_user(self, user_id: int) -> List[ProgressRecord]:
        """
        Get active progress records for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of active progress records
        """
        with db_session() as session:
            return session.query(ProgressRecord).filter_by(
                user_id=user_id
            ).filter(
                ProgressRecord.status.in_(["pending", "in_progress"])
            ).order_by(desc(ProgressRecord.updated_at)).all()
    
    def update_progress(self, record_id: int, progress_percent: float,
                       current_step: int = None, message: str = None) -> Optional[ProgressRecord]:
        """
        Update progress for a record.
        
        Args:
            record_id: The progress record ID
            progress_percent: The progress percentage (0-100)
            current_step: Optional current step
            message: Optional status message
            
        Returns:
            The updated progress record or None if not found
        """
        data = {
            "progress_percent": progress_percent,
            "updated_at": datetime.utcnow()
        }
        
        if current_step is not None:
            data["current_step"] = current_step
            
        if message is not None:
            data["message"] = message
            
        return self.update(record_id, data)
    
    def complete_progress(self, record_id: int, message: str = None) -> Optional[ProgressRecord]:
        """
        Mark a progress record as completed.
        
        Args:
            record_id: The progress record ID
            message: Optional completion message
            
        Returns:
            The updated progress record or None if not found
        """
        data = {
            "status": "completed",
            "progress_percent": 100.0,
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if message is not None:
            data["message"] = message
            
        return self.update(record_id, data)
    
    def fail_progress(self, record_id: int, error_details: str) -> Optional[ProgressRecord]:
        """
        Mark a progress record as failed.
        
        Args:
            record_id: The progress record ID
            error_details: Error details
            
        Returns:
            The updated progress record or None if not found
        """
        data = {
            "status": "failed",
            "error_details": error_details,
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        return self.update(record_id, data)


class PerformanceMetricRepository(BaseRepository):
    """Repository for PerformanceMetric operations."""
    
    def __init__(self):
        super().__init__(PerformanceMetric)
    
    def get_by_metric_type(self, metric_type: str) -> List[PerformanceMetric]:
        """
        Get metrics by type.
        
        Args:
            metric_type: The metric type
            
        Returns:
            List of metrics
        """
        with db_session() as session:
            return session.query(PerformanceMetric).filter_by(
                metric_type=metric_type
            ).order_by(desc(PerformanceMetric.timestamp)).all()
    
    def get_metrics_in_timerange(self, start_time: datetime, 
                               end_time: datetime = None) -> List[PerformanceMetric]:
        """
        Get metrics within a time range.
        
        Args:
            start_time: Start time
            end_time: End time (defaults to now)
            
        Returns:
            List of metrics in the time range
        """
        if end_time is None:
            end_time = datetime.utcnow()
            
        with db_session() as session:
            return session.query(PerformanceMetric).filter(
                PerformanceMetric.timestamp >= start_time,
                PerformanceMetric.timestamp <= end_time
            ).order_by(PerformanceMetric.timestamp).all()
    
    def get_average_by_metric_type(self, metric_type: str, 
                                 start_time: datetime = None, 
                                 end_time: datetime = None) -> float:
        """
        Get average value for a metric type in a time range.
        
        Args:
            metric_type: The metric type
            start_time: Optional start time
            end_time: Optional end time (defaults to now)
            
        Returns:
            Average metric value
        """
        if end_time is None:
            end_time = datetime.utcnow()
            
        query_filters = [PerformanceMetric.metric_type == metric_type]
        
        if start_time:
            query_filters.append(PerformanceMetric.timestamp >= start_time)
            
        query_filters.append(PerformanceMetric.timestamp <= end_time)
            
        with db_session() as session:
            result = session.query(
                func.avg(PerformanceMetric.value)
            ).filter(*query_filters).scalar()
            
            return result if result is not None else 0.0