"""
Database services for RFM-Architecture.

This module provides higher-level services that build upon the repositories
to implement business logic and integrate with the application.
"""
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from rfm.database.repository import (
    UserRepository, PresetRepository, AnimationKeyframeRepository,
    ProgressRecordRepository, PerformanceMetricRepository
)

logger = logging.getLogger(__name__)


class PresetService:
    """Service for managing fractal presets."""
    
    def __init__(self):
        self.preset_repo = PresetRepository()
        self.keyframe_repo = AnimationKeyframeRepository()
    
    def save_preset(self, name: str, fractal_type: str, parameters: Dict[str, Any],
                  description: str = None, thumbnail=None, is_public: bool = False,
                  user_id: int = None) -> Dict[str, Any]:
        """
        Save a fractal preset.
        
        Args:
            name: Preset name
            fractal_type: Fractal type (e.g., 'mandelbrot', 'julia')
            parameters: Fractal parameters as dictionary
            description: Optional description
            thumbnail: Optional thumbnail image data
            is_public: Whether the preset is public
            user_id: Optional user ID (for authenticated users)
            
        Returns:
            Dictionary representation of the created preset
        """
        preset_data = {
            "name": name,
            "fractal_type": fractal_type,
            "parameters": parameters,
            "is_public": is_public
        }
        
        if description:
            preset_data["description"] = description
            
        if thumbnail:
            preset_data["thumbnail"] = thumbnail
            
        if user_id:
            preset_data["user_id"] = user_id
        
        try:
            preset = self.preset_repo.create(preset_data)
            return self._preset_to_dict(preset)
        except Exception as e:
            logger.error(f"Failed to save preset: {e}")
            raise
    
    def get_preset(self, preset_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a preset by ID.
        
        Args:
            preset_id: Preset ID
            
        Returns:
            Dictionary representation of the preset or None if not found
        """
        preset = self.preset_repo.get_by_id(preset_id)
        if preset:
            return self._preset_to_dict(preset)
        return None
    
    def list_presets(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List presets for a user or public presets.
        
        Args:
            user_id: Optional user ID
            
        Returns:
            List of preset dictionaries
        """
        if user_id:
            presets = self.preset_repo.get_by_user(user_id)
        else:
            presets = self.preset_repo.get_public_presets()
            
        return [self._preset_to_dict(preset) for preset in presets]
    
    def update_preset(self, preset_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a preset.
        
        Args:
            preset_id: Preset ID
            data: Updated preset data
            
        Returns:
            Updated preset dictionary or None if not found
        """
        preset = self.preset_repo.update(preset_id, data)
        if preset:
            return self._preset_to_dict(preset)
        return None
    
    def delete_preset(self, preset_id: int) -> bool:
        """
        Delete a preset.
        
        Args:
            preset_id: Preset ID
            
        Returns:
            True if deleted, False if not found
        """
        return self.preset_repo.delete(preset_id)
    
    def save_animation_keyframe(self, preset_id: int, sequence_name: str,
                              time_position: float, parameters: Dict[str, Any],
                              interpolation_type: str = "linear") -> Dict[str, Any]:
        """
        Save an animation keyframe.
        
        Args:
            preset_id: Preset ID
            sequence_name: Animation sequence name
            time_position: Time position in seconds
            parameters: Parameter state at this keyframe
            interpolation_type: Interpolation type
            
        Returns:
            Dictionary representation of the created keyframe
        """
        keyframe_data = {
            "preset_id": preset_id,
            "sequence_name": sequence_name,
            "time_position": time_position,
            "parameters": parameters,
            "interpolation_type": interpolation_type
        }
        
        try:
            keyframe = self.keyframe_repo.create(keyframe_data)
            return self._keyframe_to_dict(keyframe)
        except Exception as e:
            logger.error(f"Failed to save animation keyframe: {e}")
            raise
    
    def get_animation_sequence(self, preset_id: int, sequence_name: str) -> List[Dict[str, Any]]:
        """
        Get all keyframes in an animation sequence.
        
        Args:
            preset_id: Preset ID
            sequence_name: Animation sequence name
            
        Returns:
            List of keyframe dictionaries ordered by time position
        """
        keyframes = self.keyframe_repo.get_by_sequence(preset_id, sequence_name)
        return [self._keyframe_to_dict(keyframe) for keyframe in keyframes]
    
    def _preset_to_dict(self, preset) -> Dict[str, Any]:
        """Convert a Preset model to dictionary."""
        return {
            "id": preset.id,
            "name": preset.name,
            "description": preset.description,
            "fractal_type": preset.fractal_type,
            "parameters": preset.parameters,
            "thumbnail": preset.thumbnail,
            "is_public": preset.is_public,
            "created_at": preset.created_at.isoformat() if preset.created_at else None,
            "updated_at": preset.updated_at.isoformat() if preset.updated_at else None,
            "user_id": preset.user_id
        }
    
    def _keyframe_to_dict(self, keyframe) -> Dict[str, Any]:
        """Convert an AnimationKeyframe model to dictionary."""
        return {
            "id": keyframe.id,
            "preset_id": keyframe.preset_id,
            "sequence_name": keyframe.sequence_name,
            "time_position": keyframe.time_position,
            "parameters": keyframe.parameters,
            "interpolation_type": keyframe.interpolation_type,
            "created_at": keyframe.created_at.isoformat() if keyframe.created_at else None
        }


class ProgressService:
    """Service for tracking progress of long-running operations."""
    
    def __init__(self):
        self.progress_repo = ProgressRecordRepository()
    
    def create_progress_record(self, operation_type: str, total_steps: int = None,
                             user_id: int = None, operation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new progress record.
        
        Args:
            operation_type: Type of operation (e.g., 'render', 'animation')
            total_steps: Optional total number of steps
            user_id: Optional user ID
            operation_data: Optional operation-specific data
            
        Returns:
            Dictionary representation of the created progress record
        """
        record_data = {
            "operation_type": operation_type,
            "status": "pending",
            "progress_percent": 0.0,
            "current_step": 0,
            "total_steps": total_steps,
            "operation_data": operation_data
        }
        
        if user_id:
            record_data["user_id"] = user_id
        
        try:
            record = self.progress_repo.create(record_data)
            return self._progress_to_dict(record)
        except Exception as e:
            logger.error(f"Failed to create progress record: {e}")
            raise
    
    def update_progress(self, record_id: int, progress_percent: float,
                      current_step: int = None, message: str = None) -> Optional[Dict[str, Any]]:
        """
        Update progress for a record.
        
        Args:
            record_id: Progress record ID
            progress_percent: Progress percentage (0-100)
            current_step: Optional current step
            message: Optional status message
            
        Returns:
            Updated progress record dictionary or None if not found
        """
        try:
            record = self.progress_repo.update_progress(
                record_id, progress_percent, current_step, message
            )
            
            if record:
                return self._progress_to_dict(record)
            return None
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
            raise
    
    def complete_progress(self, record_id: int, message: str = None) -> Optional[Dict[str, Any]]:
        """
        Mark a progress record as completed.
        
        Args:
            record_id: Progress record ID
            message: Optional completion message
            
        Returns:
            Updated progress record dictionary or None if not found
        """
        try:
            record = self.progress_repo.complete_progress(record_id, message)
            
            if record:
                return self._progress_to_dict(record)
            return None
        except Exception as e:
            logger.error(f"Failed to complete progress: {e}")
            raise
    
    def fail_progress(self, record_id: int, error_details: str) -> Optional[Dict[str, Any]]:
        """
        Mark a progress record as failed.
        
        Args:
            record_id: Progress record ID
            error_details: Error details
            
        Returns:
            Updated progress record dictionary or None if not found
        """
        try:
            record = self.progress_repo.fail_progress(record_id, error_details)
            
            if record:
                return self._progress_to_dict(record)
            return None
        except Exception as e:
            logger.error(f"Failed to mark progress as failed: {e}")
            raise
    
    def get_active_progress(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get active progress records for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active progress record dictionaries
        """
        records = self.progress_repo.get_active_for_user(user_id)
        return [self._progress_to_dict(record) for record in records]
    
    def get_progress(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a progress record by ID.
        
        Args:
            record_id: Progress record ID
            
        Returns:
            Progress record dictionary or None if not found
        """
        record = self.progress_repo.get_by_id(record_id)
        if record:
            return self._progress_to_dict(record)
        return None
    
    def _progress_to_dict(self, record) -> Dict[str, Any]:
        """Convert a ProgressRecord model to dictionary."""
        return {
            "id": record.id,
            "operation_type": record.operation_type,
            "status": record.status,
            "progress_percent": record.progress_percent,
            "current_step": record.current_step,
            "total_steps": record.total_steps,
            "message": record.message,
            "error_details": record.error_details,
            "operation_data": record.operation_data,
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "user_id": record.user_id
        }


class PerformanceService:
    """Service for tracking and analyzing performance metrics."""
    
    def __init__(self):
        self.metric_repo = PerformanceMetricRepository()
    
    def record_metric(self, metric_type: str, value: float, unit: str,
                    context: Dict[str, Any] = None, user_id: int = None) -> Dict[str, Any]:
        """
        Record a performance metric.
        
        Args:
            metric_type: Metric type (e.g., 'render_time', 'memory_usage', 'fps')
            value: Metric value
            unit: Metric unit (e.g., 'ms', 'MB', 'fps')
            context: Optional context information
            user_id: Optional user ID
            
        Returns:
            Dictionary representation of the created metric
        """
        metric_data = {
            "metric_type": metric_type,
            "value": value,
            "unit": unit,
            "context": context
        }
        
        if user_id:
            metric_data["user_id"] = user_id
        
        try:
            metric = self.metric_repo.create(metric_data)
            return self._metric_to_dict(metric)
        except Exception as e:
            logger.error(f"Failed to record performance metric: {e}")
            raise
    
    def get_metrics_by_type(self, metric_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent metrics by type.
        
        Args:
            metric_type: Metric type
            limit: Maximum number of records to return
            
        Returns:
            List of metric dictionaries
        """
        metrics = self.metric_repo.get_by_metric_type(metric_type)
        return [self._metric_to_dict(metric) for metric in metrics[:limit]]
    
    def get_average(self, metric_type: str, days: int = 1) -> float:
        """
        Get average metric value for the past N days.
        
        Args:
            metric_type: Metric type
            days: Number of days to look back
            
        Returns:
            Average metric value
        """
        start_time = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # Go back N days
        start_time = start_time.replace(day=start_time.day - days)
        
        return self.metric_repo.get_average_by_metric_type(metric_type, start_time)
    
    def _metric_to_dict(self, metric) -> Dict[str, Any]:
        """Convert a PerformanceMetric model to dictionary."""
        return {
            "id": metric.id,
            "metric_type": metric.metric_type,
            "value": metric.value,
            "unit": metric.unit,
            "context": metric.context,
            "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
            "user_id": metric.user_id
        }