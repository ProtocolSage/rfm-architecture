"""
Progress timeline visualization component for RFM Architecture UI.

This module provides a visual timeline component that displays historical
progress data for completed, running, and queued operations.
"""

import dearpygui.dearpygui as dpg
import time
import threading
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
import math

from rfm_ui.theme import Colors, Spacing
from rfm_ui.websocket_client import WebSocketClient, get_websocket_client, OperationStatus, OperationInfo


@dataclass
class TimelineOperation:
    """Operation data for timeline visualization."""
    
    operation_id: str
    name: str
    status: OperationStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    progress: float = 0.0
    details: Dict[str, Any] = None
    
    @property
    def is_active(self) -> bool:
        """Check if the operation is active."""
        return self.status in (
            OperationStatus.PENDING, 
            OperationStatus.RUNNING, 
            OperationStatus.PAUSED
        )
    
    @property
    def is_completed(self) -> bool:
        """Check if the operation is completed."""
        return self.status == OperationStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if the operation is failed."""
        return self.status == OperationStatus.FAILED
    
    @property
    def is_canceled(self) -> bool:
        """Check if the operation is canceled."""
        return self.status == OperationStatus.CANCELED
    
    @property
    def formatted_start_time(self) -> str:
        """Get formatted start time."""
        return datetime.fromtimestamp(self.start_time).strftime("%H:%M:%S")
    
    @property
    def formatted_end_time(self) -> str:
        """Get formatted end time."""
        if self.end_time:
            return datetime.fromtimestamp(self.end_time).strftime("%H:%M:%S")
        return "In progress"
    
    @property
    def formatted_duration(self) -> str:
        """Get formatted duration."""
        if self.duration:
            # Format as MM:SS.ms
            minutes = int(self.duration / 60)
            seconds = int(self.duration % 60)
            ms = int((self.duration * 1000) % 1000)
            return f"{minutes:02d}:{seconds:02d}.{ms:03d}"
        elif self.end_time and self.start_time:
            # Calculate duration
            duration = self.end_time - self.start_time
            minutes = int(duration / 60)
            seconds = int(duration % 60)
            ms = int((duration * 1000) % 1000)
            return f"{minutes:02d}:{seconds:02d}.{ms:03d}"
        return "Running" if self.is_active else "N/A"
    
    @property
    def status_color(self) -> Tuple[int, int, int, int]:
        """Get color for status."""
        if self.is_active:
            return Colors.PRIMARY
        elif self.is_completed:
            return Colors.SUCCESS
        elif self.is_failed:
            return Colors.ERROR
        elif self.is_canceled:
            return Colors.WARNING
        return Colors.TEXT_SECONDARY
    
    @property
    def progress_color(self) -> Tuple[int, int, int, int]:
        """Get color for progress bar."""
        if self.is_active:
            return Colors.TEAL_ACCENT
        elif self.is_completed:
            return Colors.SUCCESS
        elif self.is_failed:
            return Colors.ERROR
        elif self.is_canceled:
            return Colors.WARNING
        return Colors.TEXT_SECONDARY


class ProgressTimeline:
    """
    Visual timeline for operation progress visualization.
    
    Features:
    - Gantt-style timeline of operations
    - Color-coded status indicators
    - Hover tooltips with detailed information
    - Automatic time scaling
    - Historical data visualization
    - Real-time updates
    """
    
    def __init__(self, 
                parent_id: int,
                width: int = 700,
                height: int = 300,
                max_operations: int = 20,
                time_window_minutes: int = 10,
                websocket_client: Optional[WebSocketClient] = None,
                on_operation_click: Optional[Callable[[str], None]] = None):
        """
        Initialize the progress timeline component.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            width: Width of the timeline
            height: Height of the timeline
            max_operations: Maximum number of operations to display
            time_window_minutes: Time window to display in minutes
            websocket_client: Optional WebSocket client for real-time updates
            on_operation_click: Callback when an operation is clicked
        """
        self.parent_id = parent_id
        self.width = width
        self.height = height
        self.max_operations = max_operations
        self.time_window_minutes = time_window_minutes
        self.websocket_client = websocket_client or get_websocket_client()
        self.on_operation_click = on_operation_click
        
        # UI components
        self.container_id = None
        self.timeline_id = None
        self.header_id = None
        self.tooltip_id = None
        
        # Data
        self.operations: Dict[str, TimelineOperation] = {}
        self.visible_operations: List[TimelineOperation] = []
        self.time_range: Tuple[float, float] = (time.time() - 60 * time_window_minutes, time.time())
        
        # Create UI
        self._create_ui()
        
        # Register WebSocket callbacks
        if self.websocket_client:
            self._register_callbacks()
            
        # Start update thread
        self._stop_update_thread = False
        self._update_thread = threading.Thread(target=self._update_thread_func, daemon=True)
        self._update_thread.start()
    
    def _create_ui(self):
        """Create the timeline UI components."""
        with dpg.group(parent=self.parent_id, horizontal=False) as self.container_id:
            # Header with time labels
            with dpg.group(horizontal=True) as self.header_id:
                # Operation name column
                dpg.add_text("Operation", indent=5)
                
                # Time markers
                dpg.add_spacer(width=80)  # Space for operation names
                
                # Timeline will be drawn in the canvas
                pass
            
            # Timeline canvas
            with dpg.drawlist(width=self.width, height=self.height) as self.timeline_id:
                # Background
                dpg.draw_rectangle(
                    (0, 0),
                    (self.width, self.height),
                    color=(40, 40, 40, 255),
                    fill=(40, 40, 40, 255),
                    rounding=Spacing.RADIUS_SM
                )
                
                # Empty timeline message
                dpg.draw_text(
                    (self.width/2, self.height/2),
                    "No operations to display",
                    color=Colors.TEXT_SECONDARY,
                    size=16,
                    center=True,
                    tag="empty_timeline_text"
                )
            
            # Controls
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Clear",
                    callback=self.clear_operations
                )
                
                dpg.add_button(
                    label="Refresh",
                    callback=self._update_timeline
                )
                
                # Time window selector
                dpg.add_text("Time Window:")
                dpg.add_combo(
                    items=["5 min", "10 min", "30 min", "1 hour", "3 hours"],
                    default_value=f"{self.time_window_minutes} min",
                    callback=self._on_time_window_changed,
                    width=100
                )
        
        # Create tooltip for timeline items
        with dpg.tooltip() as self.tooltip_id:
            dpg.add_text("", tag="tooltip_name")
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text("Status: ")
                dpg.add_text("", tag="tooltip_status")
            with dpg.group(horizontal=True):
                dpg.add_text("Start: ")
                dpg.add_text("", tag="tooltip_start")
            with dpg.group(horizontal=True):
                dpg.add_text("End: ")
                dpg.add_text("", tag="tooltip_end")
            with dpg.group(horizontal=True):
                dpg.add_text("Duration: ")
                dpg.add_text("", tag="tooltip_duration")
            with dpg.group(horizontal=True):
                dpg.add_text("Progress: ")
                dpg.add_text("", tag="tooltip_progress")
    
    def _register_callbacks(self):
        """Register WebSocket callbacks."""
        if not self.websocket_client:
            return
            
        self.websocket_client.add_callback("operation_started", self._on_operation_started)
        self.websocket_client.add_callback("progress_update", self._on_progress_update)
        self.websocket_client.add_callback("operation_completed", self._on_operation_completed)
        self.websocket_client.add_callback("operation_failed", self._on_operation_failed)
        self.websocket_client.add_callback("operation_canceled", self._on_operation_canceled)
        self.websocket_client.add_callback("operations_list", self._on_operations_list)
    
    def _on_operation_started(self, data: Dict[str, Any]):
        """Handle operation started event."""
        operation = data.get("operation", {})
        operation_id = operation.get("operation_id")
        
        if not operation_id:
            return
            
        # Create operation
        self.operations[operation_id] = TimelineOperation(
            operation_id=operation_id,
            name=operation.get("name", f"Operation {operation_id}"),
            status=OperationStatus.PENDING,
            start_time=time.time(),
            progress=0.0,
            details=operation.get("details", {})
        )
        
        # Update timeline
        self._update_timeline()
    
    def _on_progress_update(self, data: Dict[str, Any]):
        """Handle progress update event."""
        progress_data = data.get("data", {})
        operation_id = progress_data.get("operation_id")
        
        if not operation_id or operation_id not in self.operations:
            return
            
        # Update operation
        operation = self.operations[operation_id]
        operation.progress = progress_data.get("progress", operation.progress) / 100.0  # Convert to 0-1
        operation.status = OperationStatus(progress_data.get("status", operation.status))
        
        if operation.details is None:
            operation.details = {}
            
        # Update details
        if "details" in progress_data and progress_data["details"]:
            operation.details.update(progress_data["details"])
            
        # Update timeline
        self._update_timeline()
    
    def _on_operation_completed(self, data: Dict[str, Any]):
        """Handle operation completed event."""
        operation_id = data.get("operation_id")
        
        if not operation_id or operation_id not in self.operations:
            return
            
        # Update operation
        operation = self.operations[operation_id]
        operation.status = OperationStatus.COMPLETED
        operation.progress = 1.0
        operation.end_time = time.time()
        operation.duration = operation.end_time - operation.start_time
        
        if operation.details is None:
            operation.details = {}
            
        # Update details
        if "details" in data and data["details"]:
            operation.details.update(data["details"])
            
        # Update timeline
        self._update_timeline()
    
    def _on_operation_failed(self, data: Dict[str, Any]):
        """Handle operation failed event."""
        operation_id = data.get("operation_id")
        
        if not operation_id or operation_id not in self.operations:
            return
            
        # Update operation
        operation = self.operations[operation_id]
        operation.status = OperationStatus.FAILED
        operation.end_time = time.time()
        operation.duration = operation.end_time - operation.start_time
        
        if operation.details is None:
            operation.details = {}
            
        # Update details
        if "details" in data and data["details"]:
            operation.details.update(data["details"])
            
        # Update timeline
        self._update_timeline()
    
    def _on_operation_canceled(self, data: Dict[str, Any]):
        """Handle operation canceled event."""
        operation_id = data.get("operation_id")
        
        if not operation_id or operation_id not in self.operations:
            return
            
        # Update operation
        operation = self.operations[operation_id]
        operation.status = OperationStatus.CANCELED
        operation.end_time = time.time()
        operation.duration = operation.end_time - operation.start_time
        
        if operation.details is None:
            operation.details = {}
            
        # Update details
        if "details" in data and data["details"]:
            operation.details.update(data["details"])
            
        # Update timeline
        self._update_timeline()
    
    def _on_operations_list(self, data: Dict[str, Any]):
        """Handle operations list event."""
        operations_data = data.get("operations", [])
        
        for op_data in operations_data:
            operation_id = op_data.get("operation_id")
            
            if not operation_id:
                continue
                
            # Create or update operation
            if operation_id in self.operations:
                # Update existing operation
                operation = self.operations[operation_id]
                operation.status = OperationStatus(op_data.get("status", operation.status))
                operation.progress = op_data.get("progress", operation.progress) / 100.0  # Convert to 0-1
                
                if "details" in op_data and op_data["details"] and operation.details is not None:
                    operation.details.update(op_data["details"])
            else:
                # Create new operation
                start_time = op_data.get("start_time", time.time())
                end_time = op_data.get("end_time")
                
                self.operations[operation_id] = TimelineOperation(
                    operation_id=operation_id,
                    name=op_data.get("name", f"Operation {operation_id}"),
                    status=OperationStatus(op_data.get("status", "pending")),
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time if end_time else None,
                    progress=op_data.get("progress", 0.0) / 100.0,  # Convert to 0-1
                    details=op_data.get("details", {})
                )
                
        # Update timeline
        self._update_timeline()
    
    def _update_thread_func(self):
        """Thread function for periodic timeline updates."""
        while not getattr(self, "_stop_update_thread", False):
            # Update time range
            self.time_range = (time.time() - 60 * self.time_window_minutes, time.time())
            
            # Update timeline
            dpg.configure_item_callback(self._update_timeline, [])
            
            # Wait
            time.sleep(1.0)
    
    def _update_timeline(self, sender=None, app_data=None):
        """Update the timeline visualization."""
        # Get visible operations (active or recently completed)
        self.visible_operations = self._get_visible_operations()
        
        # Calculate time range
        current_time = time.time()
        start_time = current_time - 60 * self.time_window_minutes
        end_time = current_time
        time_range = end_time - start_time
        
        # Delete existing timeline items
        for child in dpg.get_item_children(self.timeline_id, slot=1):
            if child != dpg.get_alias_id("empty_timeline_text"):
                dpg.delete_item(child)
                
        # Hide empty message if we have operations
        if self.visible_operations:
            dpg.configure_item("empty_timeline_text", show=False)
        else:
            dpg.configure_item("empty_timeline_text", show=True)
            return
            
        # Create new timeline
        # Draw time axis
        axis_y = 30
        axis_height = 20
        label_width = 90
        timeline_width = self.width - label_width - 10
        
        # Draw time labels
        label_count = min(int(timeline_width / 60), self.time_window_minutes)
        if label_count > 0:
            label_interval = self.time_window_minutes / label_count
            
            for i in range(label_count + 1):
                # Calculate label position
                x_pos = label_width + (i / label_count) * timeline_width
                label_time = end_time - (label_count - i) * label_interval * 60
                label_text = datetime.fromtimestamp(label_time).strftime("%H:%M:%S")
                
                # Draw label
                dpg.draw_text(
                    (x_pos, 15),
                    label_text,
                    color=Colors.TEXT_SECONDARY,
                    size=14,
                    parent=self.timeline_id
                )
                
                # Draw tick mark
                dpg.draw_line(
                    (x_pos, axis_y),
                    (x_pos, axis_y + axis_height),
                    color=Colors.LINE_SECONDARY,
                    thickness=1,
                    parent=self.timeline_id
                )
                
                # Draw grid line
                dpg.draw_line(
                    (x_pos, axis_y + axis_height),
                    (x_pos, self.height),
                    color=(60, 60, 60, 100),
                    thickness=1,
                    parent=self.timeline_id
                )
        
        # Draw operations
        row_height = 25
        row_spacing = 5
        row_total = row_height + row_spacing
        row_start_y = axis_y + axis_height + 10
        
        for i, operation in enumerate(self.visible_operations):
            # Skip if beyond visible area
            if i >= self.max_operations:
                break
                
            # Calculate row position
            row_y = row_start_y + i * row_total
            
            # Draw operation name
            dpg.draw_text(
                (5, row_y + row_height/2 - 7),
                operation.name[:15] + ("..." if len(operation.name) > 15 else ""),
                color=Colors.TEXT_PRIMARY,
                size=14,
                parent=self.timeline_id
            )
            
            # Calculate operation time range
            op_start = max(operation.start_time, start_time)
            op_end = operation.end_time or current_time
            op_end = min(op_end, end_time)
            
            # Calculate bar position
            bar_start_x = label_width + ((op_start - start_time) / time_range) * timeline_width
            bar_end_x = label_width + ((op_end - start_time) / time_range) * timeline_width
            bar_width = max(bar_end_x - bar_start_x, 3)  # Minimum width for visibility
            
            # Draw operation background bar
            bar_tag = f"op_bar_{operation.operation_id}"
            dpg.draw_rectangle(
                (bar_start_x, row_y),
                (bar_start_x + bar_width, row_y + row_height),
                color=operation.status_color,
                fill=(50, 50, 50, 200),
                rounding=3,
                tag=bar_tag,
                parent=self.timeline_id
            )
            
            # Draw progress bar
            if operation.progress > 0:
                progress_width = bar_width * operation.progress
                dpg.draw_rectangle(
                    (bar_start_x, row_y),
                    (bar_start_x + progress_width, row_y + row_height),
                    color=operation.progress_color,
                    fill=operation.progress_color,
                    rounding=3,
                    parent=self.timeline_id
                )
            
            # Draw status indicator
            status_radius = 5
            status_x = bar_end_x - status_radius - 3
            status_y = row_y + row_height/2
            
            if operation.is_completed:
                # Checkmark for completed
                dpg.draw_circle(
                    (status_x, status_y),
                    status_radius,
                    color=Colors.SUCCESS,
                    fill=Colors.SUCCESS,
                    parent=self.timeline_id
                )
                dpg.draw_text(
                    (status_x - 3, status_y - 4),
                    "✓",
                    color=(255, 255, 255, 255),
                    size=12,
                    parent=self.timeline_id
                )
            elif operation.is_failed:
                # X for failed
                dpg.draw_circle(
                    (status_x, status_y),
                    status_radius,
                    color=Colors.ERROR,
                    fill=Colors.ERROR,
                    parent=self.timeline_id
                )
                dpg.draw_text(
                    (status_x - 3, status_y - 4),
                    "✗",
                    color=(255, 255, 255, 255),
                    size=12,
                    parent=self.timeline_id
                )
            elif operation.is_canceled:
                # Slash for canceled
                dpg.draw_circle(
                    (status_x, status_y),
                    status_radius,
                    color=Colors.WARNING,
                    fill=Colors.WARNING,
                    parent=self.timeline_id
                )
                dpg.draw_text(
                    (status_x - 3, status_y - 4),
                    "⃠",
                    color=(255, 255, 255, 255),
                    size=12,
                    parent=self.timeline_id
                )
            
            # Set up tooltip for the bar
            with dpg.item_handler_registry() as handler:
                dpg.add_item_hover_handler(callback=lambda s, a, u: self._show_tooltip(a, u), user_data=operation)
                
            dpg.bind_item_handler_registry(bar_tag, handler)
            
            # Set up click handler for the bar
            if self.on_operation_click:
                dpg.configure_item(
                    bar_tag,
                    callback=self._on_operation_click,
                    user_data=operation.operation_id
                )
    
    def _get_visible_operations(self) -> List[TimelineOperation]:
        """
        Get the list of operations to display on the timeline.
        
        Returns:
            List of operations, sorted by start time (newest first)
        """
        # Calculate time range
        current_time = time.time()
        start_time = current_time - 60 * self.time_window_minutes
        
        # Filter operations by time range
        visible = []
        for op in self.operations.values():
            # Include if active or recently completed
            if op.is_active or (op.end_time and op.end_time >= start_time):
                visible.append(op)
                
        # Sort by start time (newest first)
        visible.sort(key=lambda op: op.start_time, reverse=True)
        
        # Limit to max operations
        return visible[:self.max_operations]
    
    def _show_tooltip(self, sender, user_data):
        """
        Show tooltip for an operation.
        
        Args:
            sender: Sender widget ID
            user_data: Operation data
        """
        operation = user_data
        
        # Update tooltip text
        dpg.set_value("tooltip_name", operation.name)
        dpg.set_value("tooltip_status", operation.status.value.capitalize())
        dpg.set_value("tooltip_start", operation.formatted_start_time)
        dpg.set_value("tooltip_end", operation.formatted_end_time)
        dpg.set_value("tooltip_duration", operation.formatted_duration)
        dpg.set_value("tooltip_progress", f"{operation.progress*100:.1f}%")
        
        dpg.bind_item_font("tooltip_status", 0)
        
        # Set tooltip color based on operation status
        if operation.is_completed:
            dpg.bind_item_theme("tooltip_status", dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.SUCCESS))
        elif operation.is_failed:
            dpg.bind_item_theme("tooltip_status", dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.ERROR))
        elif operation.is_canceled:
            dpg.bind_item_theme("tooltip_status", dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.WARNING))
        else:
            dpg.bind_item_theme("tooltip_status", dpg.add_theme_color(dpg.mvThemeCol_Text, Colors.PRIMARY))
    
    def _on_time_window_changed(self, sender, app_data):
        """
        Handle time window selection change.
        
        Args:
            sender: Sender widget ID
            app_data: New value
        """
        # Parse time window from string
        parts = app_data.split()
        if len(parts) != 2:
            return
            
        try:
            value = int(parts[0])
            unit = parts[1]
            
            if unit == "hour" or unit == "hours":
                value *= 60  # Convert to minutes
                
            self.time_window_minutes = value
            
            # Update time range and timeline
            self.time_range = (time.time() - 60 * self.time_window_minutes, time.time())
            self._update_timeline()
            
        except ValueError:
            pass
    
    def _on_operation_click(self, sender, app_data, user_data):
        """
        Handle operation click.
        
        Args:
            sender: Sender widget ID
            app_data: Unused
            user_data: Operation ID
        """
        if self.on_operation_click:
            self.on_operation_click(user_data)
    
    def clear_operations(self, sender=None, app_data=None):
        """Clear all operations from the timeline."""
        self.operations.clear()
        self.visible_operations.clear()
        self._update_timeline()
    
    def add_operation(self, operation: TimelineOperation):
        """
        Add an operation to the timeline.
        
        Args:
            operation: Operation to add
        """
        self.operations[operation.operation_id] = operation
        self._update_timeline()
    
    def remove_operation(self, operation_id: str):
        """
        Remove an operation from the timeline.
        
        Args:
            operation_id: ID of the operation to remove
        """
        if operation_id in self.operations:
            del self.operations[operation_id]
            self._update_timeline()
    
    def update_operation(self, operation_id: str, **kwargs):
        """
        Update an operation's properties.
        
        Args:
            operation_id: ID of the operation to update
            **kwargs: Properties to update
        """
        if operation_id in self.operations:
            operation = self.operations[operation_id]
            
            for key, value in kwargs.items():
                if hasattr(operation, key):
                    setattr(operation, key, value)
                    
            self._update_timeline()
    
    def shutdown(self):
        """Clean up resources and shut down the timeline."""
        # Stop update thread
        self._stop_update_thread = True
        if self._update_thread.is_alive():
            self._update_thread.join(timeout=1.0)
            
        # Unregister WebSocket callbacks
        if self.websocket_client:
            self.websocket_client.remove_callback("operation_started", self._on_operation_started)
            self.websocket_client.remove_callback("progress_update", self._on_progress_update)
            self.websocket_client.remove_callback("operation_completed", self._on_operation_completed)
            self.websocket_client.remove_callback("operation_failed", self._on_operation_failed)
            self.websocket_client.remove_callback("operation_canceled", self._on_operation_canceled)
            self.websocket_client.remove_callback("operations_list", self._on_operations_list)