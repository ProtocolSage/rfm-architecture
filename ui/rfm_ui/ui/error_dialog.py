"""
Error dialog UI component for RFM Architecture UI.

This module provides a UI dialog for displaying errors to users.
"""

import threading
from typing import Optional, Callable, Dict, Any

import dearpygui.dearpygui as dpg
import pyperclip

from rfm_ui.errors.types import FractalError, ErrorSeverity


class ErrorDialog:
    """UI component for displaying errors to the user."""
    
    def __init__(self, callback: Optional[Callable[[], None]] = None):
        """
        Initialize the error dialog.
        
        Args:
            callback: Optional callback to call when the user closes the dialog
        """
        self.callback = callback
        self.dialog_tag = "error_dialog"
        self.content_tag = "error_content"
        self.details_tag = "error_details"
        self.is_showing = False
        self._current_error = None
        self._lock = threading.RLock()
        
    def initialize(self) -> None:
        """Initialize the error dialog UI components."""
        with dpg.window(label="Error", tag=self.dialog_tag, 
                       width=500, height=350, show=False, 
                       modal=True, pos=(200, 200), no_resize=True):
            
            # Error icon and message
            with dpg.group(horizontal=True):
                dpg.add_text("⚠", color=(255, 0, 0), tag="error_icon")
                dpg.add_text("", tag=self.content_tag, wrap=450)
                
            # Separator
            dpg.add_separator()
            
            # Details (collapsible)
            with dpg.collapsing_header(label="Technical Details", default_open=False):
                dpg.add_text("", tag=self.details_tag, wrap=480)
                
            # Buttons
            with dpg.group(horizontal=True, pos=(150, 300)):
                dpg.add_button(label="Copy Error", callback=self._copy_error)
                dpg.add_button(label="Close", callback=self._on_close)
        
    def show_error(self, error: FractalError) -> None:
        """
        Display an error to the user.
        
        Args:
            error: The error to display
        """
        with self._lock:
            if not dpg.does_alias_exist(self.dialog_tag):
                self.initialize()
                
            # Set error message
            message = f"{error.message}"
            if error.remediation:
                message += f"\n\nSuggested action: {error.remediation}"
                
            dpg.set_value(self.content_tag, message)
            
            # Set details
            details = f"Error code: {error.error_code.value}\n"
            details += f"Severity: {error.severity.value}\n\n"
            
            if error.details:
                details += "Additional information:\n"
                for key, value in error.details.items():
                    # Skip traceback for the main view (it's too verbose)
                    if key == "traceback":
                        continue
                    details += f"  - {key}: {value}\n"
                    
            if error.original_exception:
                details += f"\nOriginal exception: {error.original_exception}"
                
            dpg.set_value(self.details_tag, details)
            
            # Set icon color based on severity
            if error.severity == ErrorSeverity.INFO:
                icon_color = (0, 255, 0)  # Green
                dpg.set_value("error_icon", "ℹ")
            elif error.severity == ErrorSeverity.WARNING:
                icon_color = (255, 255, 0)  # Yellow
                dpg.set_value("error_icon", "⚠")
            elif error.severity == ErrorSeverity.CRITICAL:
                icon_color = (255, 0, 0)  # Red
                dpg.set_value("error_icon", "⛔")
            else:  # ERROR
                icon_color = (255, 165, 0)  # Orange
                dpg.set_value("error_icon", "⚠")
                
            dpg.configure_item("error_icon", color=icon_color)
            
            # Update window title
            dpg.configure_item(self.dialog_tag, label=f"Error: {error.error_code.value}")
            
            # Show the dialog
            dpg.configure_item(self.dialog_tag, show=True)
            self.is_showing = True
            
            # Store error for copy function
            self._current_error = error
        
    def _copy_error(self) -> None:
        """Copy the error details to the clipboard."""
        if not self._current_error:
            return
            
        # Create a detailed error report
        error = self._current_error
        
        report = "Error Report\n"
        report += "===========\n\n"
        report += f"Error Code: {error.error_code.value}\n"
        report += f"Severity: {error.severity.value}\n"
        report += f"Message: {error.message}\n"
        
        if error.remediation:
            report += f"\nRemediation: {error.remediation}\n"
            
        if error.details:
            report += "\nDetails:\n"
            for key, value in error.details.items():
                report += f"  {key}: {value}\n"
                
        if error.original_exception:
            report += f"\nOriginal Exception: {error.original_exception}\n"
            
        # Copy to clipboard
        pyperclip.copy(report)
        
        # Show confirmation
        dpg.configure_item(self.content_tag, color=(0, 255, 0))
        current_text = dpg.get_value(self.content_tag)
        dpg.set_value(self.content_tag, current_text + "\n\nError details copied to clipboard.")
        
        # Reset color after a moment
        def reset_color():
            import time
            time.sleep(2)
            dpg.configure_item(self.content_tag, color=(255, 255, 255))
            
        threading.Thread(target=reset_color, daemon=True).start()
        
    def _on_close(self) -> None:
        """Handle dialog close button."""
        dpg.configure_item(self.dialog_tag, show=False)
        self.is_showing = False
        
        if self.callback:
            self.callback()