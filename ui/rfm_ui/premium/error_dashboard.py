"""Error dashboard for monitoring and managing application errors."""

import dearpygui.dearpygui as dpg
import time
from datetime import datetime

from ..components.panel import Panel
from ..errors.handler import ErrorHandler
from ..healing.recovery import RecoveryManager


class ErrorDashboard(Panel):
    """Interactive dashboard for error monitoring and management."""
    
    def __init__(self, error_handler=None, recovery_manager=None, max_errors=100):
        super().__init__("Error Dashboard", width=700, height=500)
        self.error_handler = error_handler or ErrorHandler()
        self.recovery_manager = recovery_manager or RecoveryManager()
        self.max_errors = max_errors
        self.selected_error = None
    
    def setup(self, parent=None):
        """Setup the error dashboard UI."""
        with dpg.group(parent=self.panel_id):
            # Error summary
            with dpg.group(horizontal=True):
                dpg.add_text("Total Errors: ")
                self.total_errors_text = dpg.add_text("0")
                dpg.add_spacer(width=20)
                dpg.add_text("Recoverable: ")
                self.recoverable_text = dpg.add_text("0")
                dpg.add_spacer(width=20)
                dpg.add_text("Critical: ")
                self.critical_text = dpg.add_text("0")
            
            # Error list
            with dpg.child_window(width=-1, height=200):
                self.error_table = dpg.add_table(
                    header_row=True, borders_innerH=True, borders_outerH=True, 
                    borders_innerV=True, borders_outerV=True, resizable=True,
                    callback=self._on_error_selected)
                
                dpg.add_table_column(label="Time", width_fixed=True, init_width_or_weight=150, parent=self.error_table)
                dpg.add_table_column(label="Type", width_fixed=True, init_width_or_weight=100, parent=self.error_table)
                dpg.add_table_column(label="Message", parent=self.error_table)
                dpg.add_table_column(label="Status", width_fixed=True, init_width_or_weight=100, parent=self.error_table)
            
            # Error details
            with dpg.collapsing_header(label="Error Details", default_open=True):
                dpg.add_text("Select an error to view details")
                self.error_details = dpg.add_text("")
            
            # Recovery actions
            with dpg.collapsing_header(label="Recovery Actions", default_open=True):
                with dpg.group():
                    dpg.add_text("Available recovery strategies:")
                    self.recovery_list = dpg.add_listbox(
                        items=["No strategies available"], width=-1, num_items=3)
                    dpg.add_button(label="Apply Selected Strategy", callback=self._on_apply_strategy)
            
            # Error statistics
            with dpg.collapsing_header(label="Error Statistics", default_open=False):
                with dpg.plot(label="Errors Over Time", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="error_x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Count", tag="error_y_axis")
                    self.error_series = dpg.add_line_series(
                        [], [], label="Errors", parent="error_y_axis")
        
        # Register for error notifications
        self.error_handler.add_listener(self._on_new_error)
        
        # Update periodically
        dpg.set_frame_callback(self._update_dashboard)
    
    def _update_dashboard(self):
        """Update the dashboard with current error metrics."""
        errors = self.error_handler.get_errors()
        
        # Update summary
        dpg.set_value(self.total_errors_text, str(len(errors)))
        recoverable = sum(1 for e in errors if self.recovery_manager.has_strategy(e["type"]))
        dpg.set_value(self.recoverable_text, str(recoverable))
        critical = sum(1 for e in errors if e["severity"] == "critical")
        dpg.set_value(self.critical_text, str(critical))
        
        # Update statistics graph
        timestamps = [e["timestamp"] - self.error_handler.start_time for e in errors[-50:]]
        counts = list(range(1, len(timestamps) + 1))
        dpg.set_value(self.error_series, [timestamps, counts])
    
    def _on_new_error(self, error):
        """Handle a new error event."""
        # Add to table
        with dpg.table_row(parent=self.error_table):
            error_time = datetime.fromtimestamp(error["timestamp"]).strftime("%H:%M:%S")
            dpg.add_text(error_time)
            dpg.add_text(error["type"])
            dpg.add_text(error["message"])
            
            # Status indicator
            status = "Recoverable" if self.recovery_manager.has_strategy(error["type"]) else "Unrecoverable"
            color = (0, 200, 0, 255) if status == "Recoverable" else (200, 0, 0, 255)
            with dpg.theme() as item_theme:
                with dpg.theme_component(dpg.mvText):
                    dpg.add_theme_color(dpg.mvThemeCol_Text, color)
            
            status_text = dpg.add_text(status)
            dpg.bind_item_theme(status_text, item_theme)
        
        # Auto-select first error if none selected
        if self.selected_error is None:
            self._select_error(error)
    
    def _on_error_selected(self, sender, app_data, user_data):
        """Handle error selection from the table."""
        if app_data[0] >= 0:  # Valid row selected
            error_idx = app_data[0]
            errors = self.error_handler.get_errors()
            if error_idx < len(errors):
                self._select_error(errors[error_idx])
    
    def _select_error(self, error):
        """Select and display error details."""
        self.selected_error = error
        
        # Format error details
        time_str = datetime.fromtimestamp(error["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        details = f"Time: {time_str}\n"
        details += f"Type: {error['type']}\n"
        details += f"Severity: {error['severity']}\n"
        details += f"Message: {error['message']}\n\n"
        
        if error.get("traceback"):
            details += f"Traceback:\n{error['traceback']}\n\n"
        
        if error.get("context"):
            details += "Context:\n"
            for key, value in error["context"].items():
                details += f"  {key}: {value}\n"
        
        dpg.set_value(self.error_details, details)
        
        # Update recovery strategies
        strategies = self.recovery_manager.get_strategies_for_error(error["type"])
        if strategies:
            strategy_names = [s.name for s in strategies]
            dpg.configure_item(self.recovery_list, items=strategy_names)
        else:
            dpg.configure_item(self.recovery_list, items=["No strategies available"])
    
    def _on_apply_strategy(self):
        """Apply the selected recovery strategy."""
        if not self.selected_error:
            return
        
        strategy_name = dpg.get_value(self.recovery_list)
        if strategy_name and strategy_name != "No strategies available":
            strategy = self.recovery_manager.get_strategy_by_name(strategy_name)
            if strategy:
                result = strategy.execute(context=self.selected_error.get("context", {}))
                
                # Update error status if recovery was successful
                if result:
                    self.error_handler.mark_as_resolved(self.selected_error["id"])
                    self._update_dashboard()
