"""
Progress manager component for RFM Architecture UI.

This module integrates the WebSocket client with progress UI components
to provide a complete system for real-time progress tracking.
"""

import dearpygui.dearpygui as dpg
import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, List, Set, Union

from rfm_ui.theme import Colors, Spacing, Motion
from rfm_ui.websocket_client import WebSocketClient, get_websocket_client, OperationStatus
from .progress_bar import ProgressBar

logger = logging.getLogger(__name__)


class WebSocketProgressManager:
    """
    Progress manager that integrates with WebSocket for real-time updates.
    
    This class combines the WebSocket client with progress UI components
    to display and manage operation progress.
    """
    
    def __init__(self, 
                parent_id: int,
                websocket_url: str = "ws://localhost:8765",
                show_title: bool = True,
                initial_visible: bool = True,
                max_visible_operations: int = 5):
        """
        Initialize the WebSocket progress manager.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            websocket_url: WebSocket server URL
            show_title: Whether to show the title header
            initial_visible: Whether the manager is initially visible
            max_visible_operations: Maximum number of operations to show at once
        """
        self.parent_id = parent_id
        self.websocket_url = websocket_url
        self.show_title = show_title
        self.initial_visible = initial_visible
        self.max_visible_operations = max_visible_operations
        
        # UI components
        self.container_id = None
        self.title_id = None
        self.progress_bars: Dict[str, ProgressBar] = {}
        self.connection_status_id = None
        
        # WebSocket client
        self.client = get_websocket_client(websocket_url)
        
        # Create UI
        self._create_ui()
        
        # Start WebSocket client
        self.client.start()
        
        # Register callbacks
        self._register_callbacks()
    
    def _create_ui(self) -> None:
        """Create the progress manager UI components."""
        with dpg.group(parent=self.parent_id, horizontal=False) as self.container_id:
            # Title and connection status
            if self.show_title:
                with dpg.group(horizontal=True):
                    self.title_id = dpg.add_text(
                        "Operations in Progress",
                        color=Colors.TEXT_PRIMARY
                    )
                    
                    # Spacer
                    dpg.add_spacer(width=-1)
                    
                    # Connection status
                    self.connection_status_id = dpg.add_text(
                        "Connecting...",
                        color=Colors.WARNING
                    )
                    
                # Separator
                dpg.add_separator()
                
            # Container for progress bars (empty initially)
            self.progress_container_id = dpg.add_group(horizontal=False)
            
            # Message for no operations
            self.no_operations_id = dpg.add_text(
                "No operations in progress",
                color=Colors.TEXT_SECONDARY
            )
            
        # Set initial visibility
        if not self.initial_visible:
            dpg.configure_item(self.container_id, show=False)
    
    def _register_callbacks(self) -> None:
        """Register WebSocket client callbacks."""
        self.client.add_callback("progress_update", self._on_progress_update)
        self.client.add_callback("operation_started", self._on_operation_started)
        self.client.add_callback("operation_completed", self._on_operation_completed)
        self.client.add_callback("operation_failed", self._on_operation_failed)
        self.client.add_callback("operation_canceled", self._on_operation_canceled)
        self.client.add_callback("operations_list", self._on_operations_list)
        self.client.add_callback("connection_status", self._on_connection_status)
    
    def _on_progress_update(self, data: Dict[str, Any]) -> None:
        """
        Handle progress update event.
        
        Args:
            data: Progress update data
        """
        # Get progress data
        progress_data = data.get("data", {})
        operation_id = progress_data.get("operation_id")
        
        if not operation_id:
            return
            
        # Get operation progress
        progress = progress_data.get("progress", 0.0) / 100.0  # Convert 0-100 to 0-1
        status = progress_data.get("status", "running")
        current_step = progress_data.get("current_step")
        
        # Update UI
        dpg.configure_item_callback_throttle(self._update_progress_bar, 0.1, [
            operation_id, progress, status, current_step
        ])
    
    def _on_operation_started(self, data: Dict[str, Any]) -> None:
        """
        Handle operation started event.
        
        Args:
            data: Operation started data
        """
        # Get operation data
        operation = data.get("operation", {})
        operation_id = operation.get("operation_id")
        
        if not operation_id:
            return
            
        # Get operation info
        name = operation.get("name", f"Operation {operation_id}")
        
        # Create progress bar
        self._create_progress_bar(operation_id, name)
    
    def _on_operation_completed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation completed event.
        
        Args:
            data: Operation completed data
        """
        # Get operation ID
        operation_id = data.get("operation_id")
        
        if not operation_id:
            return
            
        # Update progress bar
        if operation_id in self.progress_bars:
            progress_bar = self.progress_bars[operation_id]
            progress_bar.set_progress(1.0)  # 100%
            progress_bar.set_status("Completed")
            
            # Schedule removal after a delay
            def _remove_later():
                time.sleep(3)  # Show completed for 3 seconds
                
                # Handle in main thread
                dpg.configure_item_callback(self._remove_progress_bar, [operation_id])
                
            threading.Thread(target=_remove_later, daemon=True).start()
    
    def _on_operation_failed(self, data: Dict[str, Any]) -> None:
        """
        Handle operation failed event.
        
        Args:
            data: Operation failed data
        """
        # Get operation ID
        operation_id = data.get("operation_id")
        
        if not operation_id:
            return
            
        # Get error details
        details = data.get("details", {})
        error_message = details.get("error_message", "Operation failed")
        
        # Update progress bar
        if operation_id in self.progress_bars:
            progress_bar = self.progress_bars[operation_id]
            progress_bar.set_error(error_message)
            
            # Schedule removal after a delay
            def _remove_later():
                time.sleep(5)  # Show error for 5 seconds
                
                # Handle in main thread
                dpg.configure_item_callback(self._remove_progress_bar, [operation_id])
                
            threading.Thread(target=_remove_later, daemon=True).start()
    
    def _on_operation_canceled(self, data: Dict[str, Any]) -> None:
        """
        Handle operation canceled event.
        
        Args:
            data: Operation canceled data
        """
        # Get operation ID
        operation_id = data.get("operation_id")
        
        if not operation_id:
            return
            
        # Update progress bar
        if operation_id in self.progress_bars:
            progress_bar = self.progress_bars[operation_id]
            progress_bar.set_status("Canceled")
            
            # Schedule removal after a delay
            def _remove_later():
                time.sleep(3)  # Show canceled for 3 seconds
                
                # Handle in main thread
                dpg.configure_item_callback(self._remove_progress_bar, [operation_id])
                
            threading.Thread(target=_remove_later, daemon=True).start()
    
    def _on_operations_list(self, data: Dict[str, Any]) -> None:
        """
        Handle operations list event.
        
        Args:
            data: Operations list data
        """
        # Get operations list
        operations = data.get("operations", [])
        
        # Process each operation
        for op in operations:
            operation_id = op.get("operation_id")
            
            if not operation_id:
                continue
                
            # Get operation info
            name = op.get("name", f"Operation {operation_id}")
            status = op.get("status", "running")
            progress = op.get("progress", 0.0) / 100.0  # Convert 0-100 to 0-1
            
            # Create or update progress bar
            if operation_id not in self.progress_bars:
                self._create_progress_bar(operation_id, name)
                
            # Update progress
            self._update_progress_bar(operation_id, progress, status)
    
    def _on_connection_status(self, data: Dict[str, Any]) -> None:
        """
        Handle connection status event.
        
        Args:
            data: Connection status data
        """
        # Get status
        status = data.get("status")
        
        if not status:
            return
            
        # Update UI
        if self.connection_status_id and dpg.does_item_exist(self.connection_status_id):
            if status == "connected":
                dpg.set_value(self.connection_status_id, "Connected")
                dpg.configure_item(self.connection_status_id, color=Colors.SUCCESS)
                
                # Request operations list
                self.client.list_operations()
                
            elif status == "connecting":
                dpg.set_value(self.connection_status_id, "Connecting...")
                dpg.configure_item(self.connection_status_id, color=Colors.WARNING)
                
            elif status == "disconnected":
                dpg.set_value(self.connection_status_id, "Disconnected")
                dpg.configure_item(self.connection_status_id, color=Colors.ERROR)
    
    def _create_progress_bar(self, operation_id: str, name: str) -> None:
        """
        Create a progress bar for an operation.
        
        Args:
            operation_id: Operation ID
            name: Operation name
        """
        # Skip if already exists
        if operation_id in self.progress_bars:
            return
            
        # Create cancel callback
        def on_cancel():
            self.client.cancel_operation(operation_id)
        
        # Create progress bar
        progress_bar = ProgressBar(
            parent_id=self.progress_container_id,
            label=name,
            show_cancel=True,
            on_cancel=on_cancel,
            tag=f"progress_bar_{operation_id}"
        )
        
        # Add to dictionary
        self.progress_bars[operation_id] = progress_bar
        
        # Update UI state
        self._update_ui_state()
    
    def _update_progress_bar(self, operation_id: str, progress: float, 
                          status: str, current_step: Optional[str] = None) -> None:
        """
        Update a progress bar.
        
        Args:
            operation_id: Operation ID
            progress: Progress value (0.0 to 1.0)
            status: Operation status
            current_step: Current processing step
        """
        # Skip if doesn't exist
        if operation_id not in self.progress_bars:
            return
            
        # Get progress bar
        progress_bar = self.progress_bars[operation_id]
        
        # Update progress
        progress_bar.set_progress(progress)
        
        # Update status
        if current_step:
            progress_bar.set_status(current_step)
            
        # Handle specific statuses
        if status == "paused":
            progress_bar.set_paused(True)
        elif status == "failed":
            progress_bar.set_error()
        elif status == "canceled":
            progress_bar.set_status("Canceled")
    
    def _remove_progress_bar(self, operation_id: str) -> None:
        """
        Remove a progress bar.
        
        Args:
            operation_id: Operation ID
        """
        # Skip if doesn't exist
        if operation_id not in self.progress_bars:
            return
            
        # Get progress bar
        progress_bar = self.progress_bars[operation_id]
        
        # Get tag
        tag = f"progress_bar_{operation_id}"
        
        # Remove from UI
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
            
        # Remove from dictionary
        del self.progress_bars[operation_id]
        
        # Update UI state
        self._update_ui_state()
    
    def _update_ui_state(self) -> None:
        """Update UI state based on operations."""
        # Show/hide no operations message
        if dpg.does_item_exist(self.no_operations_id):
            dpg.configure_item(
                self.no_operations_id,
                show=(len(self.progress_bars) == 0)
            )
            
        # Show/hide container
        if self.container_id and dpg.does_item_exist(self.container_id):
            dpg.configure_item(
                self.container_id,
                show=(len(self.progress_bars) > 0 or self.initial_visible)
            )
    
    def show(self) -> None:
        """Show the progress manager."""
        if self.container_id and dpg.does_item_exist(self.container_id):
            dpg.configure_item(self.container_id, show=True)
    
    def hide(self) -> None:
        """Hide the progress manager."""
        if self.container_id and dpg.does_item_exist(self.container_id):
            dpg.configure_item(self.container_id, show=False)
    
    def is_visible(self) -> bool:
        """
        Check if the progress manager is visible.
        
        Returns:
            True if visible, False otherwise
        """
        if self.container_id and dpg.does_item_exist(self.container_id):
            return dpg.is_item_visible(self.container_id)
        return False
    
    def toggle_visibility(self) -> None:
        """Toggle the visibility of the progress manager."""
        if self.is_visible():
            self.hide()
        else:
            self.show()
    
    def clear(self) -> None:
        """Clear all progress bars."""
        # Copy keys to avoid modifying during iteration
        operation_ids = list(self.progress_bars.keys())
        
        # Remove each progress bar
        for operation_id in operation_ids:
            self._remove_progress_bar(operation_id)
    
    def shutdown(self) -> None:
        """Shut down the progress manager and WebSocket client."""
        # Stop WebSocket client
        self.client.stop()
        
        # Clear UI
        self.clear()


# Global instance
_manager_instance = None


def get_progress_manager(parent_id: int = None, websocket_url: str = "ws://localhost:8765") -> Optional[WebSocketProgressManager]:
    """
    Get the global progress manager instance.
    
    Args:
        parent_id: DearPyGui ID of the parent container
        websocket_url: WebSocket server URL
        
    Returns:
        WebSocketProgressManager instance, or None if not initialized
    """
    global _manager_instance
    
    if _manager_instance is None and parent_id is not None:
        _manager_instance = WebSocketProgressManager(parent_id, websocket_url)
        
    return _manager_instance