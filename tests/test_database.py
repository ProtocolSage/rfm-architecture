"""
Tests for the database module.

This module contains tests for the database functionality.
"""
import os
import unittest
import logging
from datetime import datetime, timedelta

# Configure test database
os.environ["RFM_DB_NAME"] = "rfm_test"
os.environ["RFM_DB_HOST"] = "localhost"
os.environ["RFM_DB_PORT"] = "5432"
os.environ["RFM_DB_USER"] = "postgres"
os.environ["RFM_DB_PASS"] = "postgres"

from rfm.database.connection import init_db, close_db_connections, db_session
from rfm.database.schema import User, Preset, AnimationKeyframe, ProgressRecord, PerformanceMetric
from rfm.database.repository import (
    UserRepository, PresetRepository, AnimationKeyframeRepository,
    ProgressRecordRepository, PerformanceMetricRepository
)
from rfm.database.service import PresetService, ProgressService, PerformanceService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseTestCase(unittest.TestCase):
    """Base test case for database tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test database."""
        # Initialize the test database
        success = init_db()
        if not success:
            raise Exception("Failed to initialize test database")

    @classmethod
    def tearDownClass(cls):
        """Clean up the test database."""
        # Close database connections
        close_db_connections()
    
    def setUp(self):
        """Set up individual tests."""
        # Clean up tables before each test
        with db_session() as session:
            session.query(AnimationKeyframe).delete()
            session.query(Preset).delete()
            session.query(ProgressRecord).delete()
            session.query(PerformanceMetric).delete()
            session.query(User).delete()
            session.commit()


class TestUserRepository(DatabaseTestCase):
    """Tests for UserRepository."""
    
    def test_create_user(self):
        """Test creating a user."""
        repo = UserRepository()
        
        # Create a test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashedpassword",
            "is_active": True
        }
        
        user = repo.create(user_data)
        
        # Verify user was created
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        
        # Verify retrieval methods
        by_id = repo.get_by_id(user.id)
        self.assertEqual(by_id.username, "testuser")
        
        by_username = repo.get_by_username("testuser")
        self.assertEqual(by_username.email, "test@example.com")
        
        by_email = repo.get_by_email("test@example.com")
        self.assertEqual(by_email.username, "testuser")
    
    def test_update_user(self):
        """Test updating a user."""
        repo = UserRepository()
        
        # Create a test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashedpassword",
            "is_active": True
        }
        
        user = repo.create(user_data)
        
        # Update the user
        updated = repo.update(user.id, {"email": "updated@example.com"})
        
        # Verify update
        self.assertEqual(updated.email, "updated@example.com")
        
        # Test update via convenience method
        updated = repo.update_last_login(user.id)
        self.assertIsNotNone(updated.last_login)
    
    def test_delete_user(self):
        """Test deleting a user."""
        repo = UserRepository()
        
        # Create a test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashedpassword",
            "is_active": True
        }
        
        user = repo.create(user_data)
        
        # Delete the user
        result = repo.delete(user.id)
        
        # Verify deletion
        self.assertTrue(result)
        self.assertIsNone(repo.get_by_id(user.id))


class TestPresetService(DatabaseTestCase):
    """Tests for PresetService."""
    
    def test_save_preset(self):
        """Test saving a preset."""
        service = PresetService()
        
        # Create a test preset
        preset = service.save_preset(
            name="Test Preset",
            fractal_type="mandelbrot",
            parameters={"zoom": 1.0, "center_x": 0.0, "center_y": 0.0},
            description="A test preset",
            is_public=True
        )
        
        # Verify preset was created
        self.assertIsNotNone(preset)
        self.assertEqual(preset["name"], "Test Preset")
        self.assertEqual(preset["fractal_type"], "mandelbrot")
        self.assertEqual(preset["parameters"]["zoom"], 1.0)
        
        # Test retrieval
        retrieved = service.get_preset(preset["id"])
        self.assertEqual(retrieved["name"], "Test Preset")
        
        # Test listing
        presets = service.list_presets()
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]["name"], "Test Preset")
    
    def test_animation_keyframes(self):
        """Test saving and retrieving animation keyframes."""
        service = PresetService()
        
        # Create a test preset
        preset = service.save_preset(
            name="Animation Test",
            fractal_type="mandelbrot",
            parameters={"zoom": 1.0, "center_x": 0.0, "center_y": 0.0}
        )
        
        # Add keyframes
        keyframe1 = service.save_animation_keyframe(
            preset_id=preset["id"],
            sequence_name="zoom_in",
            time_position=0.0,
            parameters={"zoom": 1.0}
        )
        
        keyframe2 = service.save_animation_keyframe(
            preset_id=preset["id"],
            sequence_name="zoom_in",
            time_position=1.0,
            parameters={"zoom": 2.0}
        )
        
        # Retrieve sequence
        sequence = service.get_animation_sequence(preset["id"], "zoom_in")
        
        # Verify sequence
        self.assertEqual(len(sequence), 2)
        self.assertEqual(sequence[0]["time_position"], 0.0)
        self.assertEqual(sequence[1]["time_position"], 1.0)
        self.assertEqual(sequence[0]["parameters"]["zoom"], 1.0)
        self.assertEqual(sequence[1]["parameters"]["zoom"], 2.0)


class TestProgressService(DatabaseTestCase):
    """Tests for ProgressService."""
    
    def test_progress_tracking(self):
        """Test progress tracking."""
        service = ProgressService()
        
        # Create a progress record
        record = service.create_progress_record(
            operation_type="render",
            total_steps=10,
            operation_data={"filename": "test.png"}
        )
        
        # Verify record was created
        self.assertIsNotNone(record)
        self.assertEqual(record["operation_type"], "render")
        self.assertEqual(record["status"], "pending")
        self.assertEqual(record["progress_percent"], 0.0)
        
        # Update progress
        updated = service.update_progress(
            record_id=record["id"],
            progress_percent=50.0,
            current_step=5,
            message="Halfway there"
        )
        
        # Verify update
        self.assertEqual(updated["progress_percent"], 50.0)
        self.assertEqual(updated["current_step"], 5)
        self.assertEqual(updated["message"], "Halfway there")
        
        # Complete
        completed = service.complete_progress(
            record_id=record["id"],
            message="Done"
        )
        
        # Verify completion
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["progress_percent"], 100.0)
        self.assertEqual(completed["message"], "Done")
        
        # Test retrieval
        retrieved = service.get_progress(record["id"])
        self.assertEqual(retrieved["status"], "completed")


class TestPerformanceService(DatabaseTestCase):
    """Tests for PerformanceService."""
    
    def test_performance_metrics(self):
        """Test recording and retrieving performance metrics."""
        service = PerformanceService()
        
        # Record metrics
        metric1 = service.record_metric(
            metric_type="render_time",
            value=100.5,
            unit="ms",
            context={"resolution": "512x512"}
        )
        
        metric2 = service.record_metric(
            metric_type="render_time",
            value=150.2,
            unit="ms",
            context={"resolution": "512x512"}
        )
        
        # Get metrics
        metrics = service.get_metrics_by_type("render_time")
        
        # Verify metrics
        self.assertEqual(len(metrics), 2)
        self.assertEqual(metrics[0]["value"], 150.2)  # Most recent first
        self.assertEqual(metrics[1]["value"], 100.5)
        
        # Test average
        avg = service.get_average("render_time")
        self.assertAlmostEqual(avg, 125.35, places=1)


if __name__ == "__main__":
    unittest.main()