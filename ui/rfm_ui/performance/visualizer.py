"""
Performance visualization for RFM Architecture UI.

This module provides UI components for visualizing performance metrics.
"""

from typing import List, Dict, Any, Optional, Tuple, Set, Callable
import time
import numpy as np
import threading
import dearpygui.dearpygui as dpg
import matplotlib.pyplot as plt
from io import BytesIO
import base64

from .tracker import PerformanceTracker, PerformanceRecord


class PerformanceVisualizer:
    """UI Component for displaying performance metrics."""
    
    def __init__(self, performance_tracker: PerformanceTracker, update_interval_ms: int = 1000):
        """
        Initialize the performance visualizer.
        
        Args:
            performance_tracker: Performance tracker to visualize
            update_interval_ms: Interval for automatic updates
        """
        self.tracker = performance_tracker
        self.update_interval = update_interval_ms
        self.visible = False
        self.window_tag = "performance_window"
        self.operations: Set[str] = set()
        self.selected_operation: Optional[str] = None
        self.active_tab = 0
        self.last_update = 0
        self.is_updating = False
        self.update_timer = None
        
    def initialize(self) -> None:
        """Initialize the performance view UI components."""
        # Create the window
        with dpg.window(label="Performance Monitor", tag=self.window_tag, 
                       width=800, height=600, show=False, pos=(100, 50)):
            
            # Add tabs for different views
            with dpg.tab_bar(callback=self._on_tab_change, tag="perf_tab_bar"):
                # Overview tab
                with dpg.tab(label="Overview", tag="tab_overview"):
                    dpg.add_text("Performance Overview")
                    dpg.add_separator()
                    
                    # Stats and metrics
                    with dpg.group(horizontal=True):
                        dpg.add_text("Time Window:")
                        dpg.add_combo(
                            items=["Last 1 minute", "Last 5 minutes", "Last 15 minutes", "All data"],
                            default_value="Last 5 minutes",
                            callback=self._update_overview,
                            width=150,
                            tag="overview_time_window"
                        )
                    
                    # Overview table
                    with dpg.table(header_row=True, resizable=True, 
                                  policy=dpg.mvTable_SizingStretchProp,
                                  borders_outerH=True, borders_innerH=True, 
                                  borders_innerV=True, borders_outerV=True,
                                  tag="overview_table"):
                        # Add columns
                        dpg.add_table_column(label="Operation")
                        dpg.add_table_column(label="Count")
                        dpg.add_table_column(label="Avg (ms)")
                        dpg.add_table_column(label="Min (ms)")
                        dpg.add_table_column(label="Max (ms)")
                        dpg.add_table_column(label="P95 (ms)")
                        dpg.add_table_column(label="Mem (MB)")
                
                # Time Series tab
                with dpg.tab(label="Time Series", tag="tab_timeseries"):
                    dpg.add_text("Performance Timeline")
                    dpg.add_separator()
                    
                    # Operation selector
                    with dpg.group(horizontal=True):
                        dpg.add_text("Operation:")
                        dpg.add_combo(
                            items=[],
                            callback=self._on_operation_selected,
                            width=250,
                            tag="operation_selector"
                        )
                    
                    # Plot
                    with dpg.plot(height=-1, width=-1, tag="timeline_plot"):
                        # Axes
                        dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="x_axis")
                        dpg.add_plot_axis(dpg.mvYAxis, label="Duration (ms)", tag="y_axis")
                        
                        # We'll add series dynamically
                        dpg.add_line_series([], [], label="Duration", tag="duration_series", parent="y_axis")
                
                # Hotspots tab
                with dpg.tab(label="Hotspots", tag="tab_hotspots"):
                    dpg.add_text("Performance Hotspots")
                    dpg.add_separator()
                    
                    # Threshold control
                    with dpg.group(horizontal=True):
                        dpg.add_text("Threshold (ms):")
                        dpg.add_slider_int(
                            default_value=100, 
                            min_value=10, 
                            max_value=1000,
                            callback=self._update_hotspots,
                            width=150,
                            tag="hotspot_threshold"
                        )
                    
                    # Hotspots table
                    with dpg.table(header_row=True, resizable=True, 
                                  policy=dpg.mvTable_SizingStretchProp,
                                  borders_outerH=True, borders_innerH=True, 
                                  borders_innerV=True, borders_outerV=True,
                                  tag="hotspots_table"):
                        # Add columns
                        dpg.add_table_column(label="Operation")
                        dpg.add_table_column(label="Duration (ms)")
                        dpg.add_table_column(label="Memory (MB)")
                        dpg.add_table_column(label="Time")
                
                # Regressions tab
                with dpg.tab(label="Regressions", tag="tab_regressions"):
                    dpg.add_text("Performance Regressions")
                    dpg.add_separator()
                    
                    # Controls
                    with dpg.group(horizontal=True):
                        dpg.add_text("Regression Threshold (%):")
                        dpg.add_slider_float(
                            default_value=20.0, 
                            min_value=5.0, 
                            max_value=100.0,
                            callback=self._update_regressions,
                            width=150,
                            tag="regression_threshold"
                        )
                        dpg.add_button(
                            label="Set Current as Baseline", 
                            callback=self._set_baseline
                        )
                    
                    # Regressions table
                    with dpg.table(header_row=True, resizable=True, 
                                  policy=dpg.mvTable_SizingStretchProp,
                                  borders_outerH=True, borders_innerH=True, 
                                  borders_innerV=True, borders_outerV=True,
                                  tag="regressions_table"):
                        # Add columns
                        dpg.add_table_column(label="Operation")
                        dpg.add_table_column(label="Metric")
                        dpg.add_table_column(label="Baseline")
                        dpg.add_table_column(label="Current")
                        dpg.add_table_column(label="Regression (%)")
            
            # Footer with controls
            with dpg.group(horizontal=True):
                dpg.add_button(label="Refresh", callback=self._update_all)
                dpg.add_checkbox(label="Auto Refresh", default_value=True, callback=self._toggle_auto_refresh, tag="auto_refresh")
                dpg.add_button(label="Export Report", callback=self._export_report)
                dpg.add_button(label="Close", callback=lambda: self.toggle_visibility())
        
        # Setup auto-refresh
        self._start_auto_refresh()
            
    def toggle_visibility(self) -> None:
        """Toggle visibility of the performance visualizer."""
        self.visible = not self.visible
        dpg.configure_item(self.window_tag, show=self.visible)
        
        # Force update when shown
        if self.visible:
            self._update_all()
            
    def _on_tab_change(self, sender, app_data) -> None:
        """Handle tab change."""
        self.active_tab = app_data
        self._update_all()
            
    def _update_all(self, sender=None, app_data=None) -> None:
        """Update all performance views."""
        if not self.visible or self.is_updating:
            return
            
        self.is_updating = True
        try:
            # Update time since last update
            now = time.time()
            if now - self.last_update < 0.1:  # Prevent too frequent updates
                return
                
            self.last_update = now
                
            # Update operations list
            self._update_operations_list()
            
            # Update active tab
            active_tab = dpg.get_value("perf_tab_bar")
            if active_tab == 0:
                self._update_overview()
            elif active_tab == 1:
                self._update_timeseries()
            elif active_tab == 2:
                self._update_hotspots()
            elif active_tab == 3:
                self._update_regressions()
        finally:
            self.is_updating = False
        
    def _update_operations_list(self) -> None:
        """Update the operations list in the selector."""
        # Get performance history
        history = self.tracker.get_history()
        operations = set(r.operation for r in history)
        
        # Only update if there are new operations
        if operations == self.operations:
            return
            
        self.operations = operations
        
        # Update the combo
        dpg.configure_item("operation_selector", items=list(operations))
        
        # If no operation is selected, select the first one
        if self.selected_operation is None and operations:
            self.selected_operation = next(iter(operations))
            dpg.set_value("operation_selector", self.selected_operation)
            
    def _on_operation_selected(self, sender, app_data) -> None:
        """Handle operation selection."""
        self.selected_operation = app_data
        self._update_timeseries()
        
    def _update_overview(self, sender=None, app_data=None) -> None:
        """Update the overview table."""
        # Clear existing rows
        if dpg.does_alias_exist("overview_table"):
            # Delete existing rows
            for row in dpg.get_item_children("overview_table", 1):
                dpg.delete_item(row)
        
        # Get all operation stats
        stats = self.tracker.get_all_operation_stats()
        
        # Filter by time window if specified
        time_window = dpg.get_value("overview_time_window")
        if time_window != "All data":
            # Extract time window in minutes
            if time_window == "Last 1 minute":
                window_minutes = 1
            elif time_window == "Last 5 minutes":
                window_minutes = 5
            elif time_window == "Last 15 minutes":
                window_minutes = 15
            else:
                window_minutes = None
                
            if window_minutes:
                # Get current time
                now = time.time()
                
                # Filter history by time window
                history = [r for r in self.tracker.get_history() 
                          if now - r.timestamp <= window_minutes * 60]
                
                # Get operations in this window
                operations = set(r.operation for r in history)
                
                # Only show stats for operations in this window
                stats = {op: stat for op, stat in stats.items() if op in operations}
        
        # Sort operations by average duration
        sorted_ops = sorted(
            [(op, data) for op, data in stats.items()],
            key=lambda x: x[1].get("avg_duration_ms", 0),
            reverse=True
        )
        
        # Add rows for each operation
        for op, data in sorted_ops:
            with dpg.table_row(parent="overview_table"):
                dpg.add_text(op)
                dpg.add_text(f"{data.get('count', 0)}")
                dpg.add_text(f"{data.get('avg_duration_ms', 0):.2f}")
                dpg.add_text(f"{data.get('min_duration_ms', 0):.2f}")
                dpg.add_text(f"{data.get('max_duration_ms', 0):.2f}")
                dpg.add_text(f"{data.get('p95_duration_ms', 0):.2f}")
                dpg.add_text(f"{data.get('avg_memory_usage_mb', 0):.2f}")
                
    def _update_timeseries(self, sender=None, app_data=None) -> None:
        """Update the time series plot."""
        # Get selected operation
        selected_op = self.selected_operation
        if not selected_op:
            return
            
        # Get history for this operation
        history = self.tracker.get_history()
        op_history = [r for r in history if r.operation == selected_op]
        
        if not op_history:
            return
            
        # Extract timestamps and durations
        timestamps = np.array([r.timestamp for r in op_history])
        durations = np.array([r.duration_ms for r in op_history])
        
        # Normalize timestamps to start at 0
        if len(timestamps) > 0:
            timestamps = timestamps - timestamps.min()
        
        # Update the plot
        if dpg.does_alias_exist("duration_series"):
            dpg.set_value("duration_series", [timestamps.tolist(), durations.tolist()])
            
            # Set axis limits
            max_time = max(timestamps) if len(timestamps) > 0 else 1
            max_duration = max(durations) * 1.1 if len(durations) > 0 else 100
            
            dpg.set_axis_limits("x_axis", 0, max_time)
            dpg.set_axis_limits("y_axis", 0, max_duration)
        
    def _update_hotspots(self, sender=None, app_data=None) -> None:
        """Update the hotspots table."""
        # Get threshold
        threshold = dpg.get_value("hotspot_threshold")
        if threshold is None:
            threshold = 100
            
        # Get hotspots
        hotspots = self.tracker.get_hotspots(threshold)
        
        # Sort by duration
        hotspots.sort(key=lambda x: x.duration_ms, reverse=True)
        
        # Clear existing rows
        if dpg.does_alias_exist("hotspots_table"):
            # Delete existing rows
            for row in dpg.get_item_children("hotspots_table", 1):
                dpg.delete_item(row)
        
        # Add rows for each hotspot (limit to 100)
        for hs in hotspots[:100]:
            with dpg.table_row(parent="hotspots_table"):
                dpg.add_text(hs.operation)
                dpg.add_text(f"{hs.duration_ms:.2f}")
                memory_usage = hs.memory_after_mb - hs.memory_before_mb
                dpg.add_text(f"{memory_usage:.2f}")
                time_str = time.strftime("%H:%M:%S", time.localtime(hs.timestamp))
                dpg.add_text(time_str)
                
    def _set_baseline(self, sender=None, app_data=None) -> None:
        """Set current as baseline."""
        success = self.tracker.set_current_as_baseline()
        if success:
            self._update_regressions()
            dpg.add_text("Baseline set successfully!", color=[0, 255, 0], parent="tab_regressions")
        else:
            dpg.add_text("Failed to set baseline!", color=[255, 0, 0], parent="tab_regressions")
        
    def _update_regressions(self, sender=None, app_data=None) -> None:
        """Update the regressions table."""
        # Get threshold
        threshold = dpg.get_value("regression_threshold")
        if threshold is None:
            threshold = 20.0
            
        # Get regressions
        regressions = self.tracker.detect_performance_regressions(threshold)
        
        # Clear existing rows
        if dpg.does_alias_exist("regressions_table"):
            # Delete existing rows
            for row in dpg.get_item_children("regressions_table", 1):
                dpg.delete_item(row)
        
        # Add rows for each regression
        for reg in regressions:
            with dpg.table_row(parent="regressions_table"):
                dpg.add_text(reg["operation"])
                dpg.add_text(reg["metric"])
                dpg.add_text(f"{reg['baseline_value']:.2f}")
                dpg.add_text(f"{reg['current_value']:.2f}")
                # Use color to indicate severity
                if reg["regression_pct"] > 100:
                    color = [255, 0, 0]  # Red for severe
                elif reg["regression_pct"] > 50:
                    color = [255, 165, 0]  # Orange for significant
                else:
                    color = [255, 255, 0]  # Yellow for moderate
                dpg.add_text(f"{reg['regression_pct']:.2f}", color=color)
                
    def _export_report(self, sender=None, app_data=None) -> None:
        """Export a performance report."""
        # Generate report
        report = self.tracker.generate_report()
        
        try:
            # Create a timestamp for the filename
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            filename = f"performance_report_{timestamp}.json"
            
            # Save report to file
            import json
            import os
            
            # Ensure log directory exists
            log_dir = self.tracker._save_path
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            filepath = os.path.join(log_dir, filename)
            with open(filepath, "w") as f:
                json.dump(report, f, indent=2)
                
            dpg.add_text(f"Report exported to {filepath}", color=[0, 255, 0], parent=self.window_tag)
        except Exception as e:
            dpg.add_text(f"Failed to export report: {e}", color=[255, 0, 0], parent=self.window_tag)
            
    def _toggle_auto_refresh(self, sender=None, app_data=None) -> None:
        """Toggle auto refresh."""
        auto_refresh = dpg.get_value("auto_refresh")
        
        if auto_refresh:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()
            
    def _start_auto_refresh(self) -> None:
        """Start auto refresh."""
        if self.update_timer:
            return
            
        self.update_timer = threading.Timer(self.update_interval / 1000, self._auto_refresh_callback)
        self.update_timer.daemon = True
        self.update_timer.start()
            
    def _stop_auto_refresh(self) -> None:
        """Stop auto refresh."""
        if self.update_timer:
            self.update_timer.cancel()
            self.update_timer = None
            
    def _auto_refresh_callback(self) -> None:
        """Callback for auto refresh."""
        if not dpg.is_dearpygui_running():
            return
            
        # Update the UI if visible
        if self.visible:
            self._update_all()
            
        # Schedule next update
        if dpg.get_value("auto_refresh"):
            self.update_timer = threading.Timer(self.update_interval / 1000, self._auto_refresh_callback)
            self.update_timer.daemon = True
            self.update_timer.start()