"""Performance dashboard for monitoring and visualizing application performance."""

import dearpygui.dearpygui as dpg
import numpy as np
import time
from collections import deque

from ..performance.tracker import PerformanceTracker
from ..components.panel import Panel


class PerformanceDashboard(Panel):
    """Interactive dashboard for real-time performance monitoring."""
    
    def __init__(self, tracker=None, max_history=300):
        super().__init__("Performance Dashboard", width=600, height=400)
        self.tracker = tracker or PerformanceTracker()
        self.max_history = max_history
        self.render_times = deque(maxlen=max_history)
        self.memory_usage = deque(maxlen=max_history)
        self.fps_history = deque(maxlen=max_history)
        self.timestamps = deque(maxlen=max_history)
        self.last_update = time.time()
        self.update_interval = 0.5  # seconds
        
    def setup(self, parent=None):
        """Setup the performance dashboard UI."""
        with dpg.collapsing_header(label="Performance Metrics", default_open=True, parent=self.panel_id):
            # Summary metrics
            with dpg.group(horizontal=True):
                dpg.add_text("FPS: ")
                self.fps_text = dpg.add_text("0")
                dpg.add_spacer(width=20)
                dpg.add_text("Render time: ")
                self.render_time_text = dpg.add_text("0 ms")
                dpg.add_spacer(width=20)
                dpg.add_text("Memory: ")
                self.memory_text = dpg.add_text("0 MB")
            
            # FPS Graph
            with dpg.plot(label="FPS", height=150, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="fps_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="FPS", tag="fps_y_axis")
                self.fps_series = dpg.add_line_series(
                    [], [], label="FPS", parent="fps_y_axis")
            
            # Render Time Graph
            with dpg.plot(label="Render Time", height=150, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="render_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="ms", tag="render_y_axis")
                self.render_series = dpg.add_line_series(
                    [], [], label="Render Time", parent="render_y_axis")
        
        # Hotspots section
        with dpg.collapsing_header(label="Performance Hotspots", default_open=True, parent=self.panel_id):
            self.hotspots_table = dpg.add_table(
                header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True,
                borders_outerV=True, resizable=True, policy=dpg.mvTable_SizingStretchProp)
            
            dpg.add_table_column(label="Function", parent=self.hotspots_table)
            dpg.add_table_column(label="Calls", parent=self.hotspots_table)
            dpg.add_table_column(label="Total Time (ms)", parent=self.hotspots_table)
            dpg.add_table_column(label="Avg Time (ms)", parent=self.hotspots_table)
            dpg.add_table_column(label="% of Total", parent=self.hotspots_table)
        
        # Register update callback
        dpg.set_frame_callback(self._update_dashboard)
    
    def _update_dashboard(self):
        """Update the dashboard with current performance metrics."""
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
        
        self.last_update = current_time
        
        # Get latest metrics
        metrics = self.tracker.get_current_metrics()
        
        # Update history
        self.render_times.append(metrics.get("render_time_ms", 0))
        self.memory_usage.append(metrics.get("memory_mb", 0))
        self.fps_history.append(metrics.get("fps", 0))
        self.timestamps.append(current_time - self.tracker.start_time)
        
        # Update text displays
        dpg.set_value(self.fps_text, f"{metrics.get('fps', 0):.1f}")
        dpg.set_value(self.render_time_text, f"{metrics.get('render_time_ms', 0):.2f} ms")
        dpg.set_value(self.memory_text, f"{metrics.get('memory_mb', 0):.1f} MB")
        
        # Update graphs
        dpg.set_value(self.fps_series, [list(self.timestamps), list(self.fps_history)])
        dpg.set_value(self.render_series, [list(self.timestamps), list(self.render_times)])
        
        # Update hotspots table
        self._update_hotspots(metrics.get("hotspots", []))
    
    def _update_hotspots(self, hotspots):
        """Update the hotspots table with current function timing data."""
        # Clear existing rows
        for child in dpg.get_item_children(self.hotspots_table, slot=1):
            dpg.delete_item(child)
        
        # Add new rows
        total_time = sum(h.get("total_time_ms", 0) for h in hotspots)
        
        for hotspot in sorted(hotspots, key=lambda x: x.get("total_time_ms", 0), reverse=True)[:10]:
            with dpg.table_row(parent=self.hotspots_table):
                dpg.add_text(hotspot.get("function_name", "Unknown"))
                dpg.add_text(str(hotspot.get("calls", 0)))
                dpg.add_text(f"{hotspot.get('total_time_ms', 0):.2f}")
                avg_time = hotspot.get("total_time_ms", 0) / max(1, hotspot.get("calls", 1))
                dpg.add_text(f"{avg_time:.2f}")
                percent = (hotspot.get("total_time_ms", 0) / max(0.001, total_time)) * 100
                dpg.add_text(f"{percent:.1f}%")
    
    def save_snapshot(self, filepath):
        """Save current performance metrics to a file.
        
        Args:
            filepath: Path to save the performance snapshot
        """
        self.tracker.save_snapshot(filepath)
