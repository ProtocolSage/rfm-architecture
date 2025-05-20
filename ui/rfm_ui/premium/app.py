"""Premium UI application module with enhanced features."""

import dearpygui.dearpygui as dpg
import asyncio
import time
import uuid

from ..ui.app import BaseApp
from ..components.progress_bar import ProgressBar
from ..components.fps_overlay import FPSOverlay
from ..performance.tracker import PerformanceTracker
from ..theme.premium_theme import apply_premium_theme
from ..errors.handler import ErrorHandler
from ..healing.recovery import RecoveryManager


class PremiumApp(BaseApp):
    """Enhanced application with premium features like performance monitoring,
    error handling, and self-healing capabilities."""
    
    def __init__(self, title="RFM Architecture Premium", width=1280, height=800):
        super().__init__(title, width, height)
        self.session_id = str(uuid.uuid4())
        self.performance_tracker = PerformanceTracker()
        self.error_handler = ErrorHandler()
        self.recovery_manager = RecoveryManager()
        self.fps_overlay = None
        self.progress_bar = None
        
    def setup(self):
        """Setup the premium application with enhanced features."""
        super().setup()
        
        # Apply premium theme
        apply_premium_theme()
        
        # Initialize premium components
        self._setup_fps_overlay()
        self._setup_progress_bar()
        self._setup_performance_monitoring()
        
        # Register error handling
        self.error_handler.register_global_handlers()
        
    def _setup_fps_overlay(self):
        """Setup FPS overlay for performance monitoring."""
        self.fps_overlay = FPSOverlay()
        self.fps_overlay.setup(corner="top-right")
        
    def _setup_progress_bar(self):
        """Setup progress bar for operations."""
        self.progress_bar = ProgressBar()
        self.progress_bar.setup(parent="main_window")
        
    def _setup_performance_monitoring(self):
        """Setup performance monitoring integration."""
        self.performance_tracker.start()
        
        # Add performance monitoring callback
        dpg.set_frame_callback(self._on_frame)
        
    def _on_frame(self):
        """Called every frame to update performance metrics."""
        # Update FPS and performance metrics
        if self.fps_overlay:
            self.fps_overlay.update()
            
        # Track render times
        self.performance_tracker.record_frame()
        
    def show_progress(self, progress, message=""):
        """Show progress in the progress bar.
        
        Args:
            progress: Float between 0.0 and 1.0
            message: Optional message to display
        """
        if self.progress_bar:
            self.progress_bar.update(progress, message)
    
    def on_error(self, error_type, message, context=None):
        """Handle application errors.
        
        Args:
            error_type: Type of error
            message: Error message
            context: Additional context information
        """
        # Log the error
        self.error_handler.handle(error_type, message, context)
        
        # Attempt self-healing if possible
        recovery_action = self.recovery_manager.get_recovery_strategy(error_type, context)
        if recovery_action:
            return recovery_action.execute()
        
        return False
    
    def run(self):
        """Run the premium application with enhanced error handling."""
        try:
            super().run()
        except Exception as e:
            self.error_handler.handle("runtime", str(e))
        finally:
            self.performance_tracker.stop()
            self.performance_tracker.save_session_metrics(self.session_id)
