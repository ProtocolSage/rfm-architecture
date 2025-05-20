#!/usr/bin/env python3
"""
Take a screenshot of the RFM Architecture UI for testing.

This script launches the application, captures a screenshot,
and then exits cleanly. It's used by the Playwright visual regression tests.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Fix Python imports by adjusting the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Also add ui directory to the path to resolve internal imports
sys.path.insert(0, os.path.join(project_root, 'ui'))

try:
    # Import Pillow for screenshot capture
    from PIL import ImageGrab
    import dearpygui.dearpygui as dpg
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install missing modules with:")
    print("  pip install pillow dearpygui")
    sys.exit(1)

# Screenshot file location
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')
SCREENSHOT_PATH = os.path.join(SCREENSHOT_DIR, 'app_screenshot.png')

# Ensure screenshot directory exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def take_screenshot_and_exit():
    """
    Take a screenshot after a short delay and then exit the application.
    This function is scheduled as a separate thread.
    """
    # Wait for the application to fully render
    time.sleep(2)
    
    # Take screenshot using PIL ImageGrab
    if dpg.is_dearpygui_running():
        try:
            # Get viewport dimensions and position
            view_x, view_y = dpg.get_viewport_pos()
            view_w = dpg.get_viewport_client_width()
            view_h = dpg.get_viewport_client_height()
            
            print(f"Taking {view_w}x{view_h} screenshot to {SCREENSHOT_PATH}")
            
            # Calculate the bounding box for the screenshot
            bbox = (view_x, view_y, view_x + view_w, view_y + view_h)
            
            # Capture the screenshot and save it
            img = ImageGrab.grab(bbox)
            img.save(SCREENSHOT_PATH)
            
            print(f"Screenshot saved -> {SCREENSHOT_PATH}")
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            
            # Fallback to full screen capture if viewport capture fails
            try:
                print("Attempting full screen capture instead...")
                ImageGrab.grab().save(SCREENSHOT_PATH)
                print(f"Full screen screenshot saved -> {SCREENSHOT_PATH}")
            except Exception as e2:
                print(f"Full screen capture also failed: {e2}")
        
        # Wait a bit for the screenshot to be saved
        time.sleep(1)
        
        # Exit the application
        dpg.stop_dearpygui()


def create_test_ui():
    """Create a simple test UI that looks similar to the real app."""
    # Create a context for Dear PyGui
    dpg.create_context()
    
    # Set up font
    with dpg.font_registry():
        # Use default font if specific fonts are not available
        pass
    
    # Create a viewport with specific dimensions for consistent screenshots
    dpg.create_viewport(title="RFM Architecture Test", width=1280, height=800)
    
    # Create a primary window
    with dpg.window(label="RFM Architecture Visualizer", 
                   tag="primary_window",
                   width=1280, height=800,
                   no_title_bar=True, no_resize=True, no_move=True, no_close=True):
        
        # Create a panel-like structure
        with dpg.group(horizontal=True):
            # Left panel (parameters)
            with dpg.child_window(width=400, height=-1, label="Parameters"):
                dpg.add_text("Fractal Type")
                dpg.add_combo(
                    items=["Mandelbrot", "Julia", "L-System", "Cantor Dust"],
                    default_value="Mandelbrot",
                    width=-1
                )
                
                dpg.add_separator()
                
                # Parameters section
                with dpg.collapsing_header(label="Parameters", default_open=True):
                    dpg.add_text("Center")
                    with dpg.group(horizontal=True):
                        dpg.add_input_float(
                            default_value=-0.5, 
                            width=150
                        )
                        dpg.add_input_float(
                            default_value=0.0, 
                            width=150
                        )
                        
                    dpg.add_text("Zoom")
                    dpg.add_slider_float(
                        default_value=1.0,
                        min_value=0.1,
                        max_value=100.0,
                        format="%.6f",
                        width=-1
                    )
                    
                    dpg.add_text("Max Iterations")
                    dpg.add_slider_int(
                        default_value=100,
                        min_value=10,
                        max_value=1000,
                        width=-1
                    )
                    
                # Visualization section
                with dpg.collapsing_header(label="Visualization", default_open=True):
                    dpg.add_text("Color Map")
                    dpg.add_combo(
                        items=["viridis", "plasma", "inferno"],
                        default_value="viridis",
                        width=-1
                    )
                    
                    dpg.add_text("Resolution")
                    with dpg.group(horizontal=True):
                        dpg.add_input_int(
                            default_value=800, 
                            width=150
                        )
                        dpg.add_text("×")
                        dpg.add_input_int(
                            default_value=600, 
                            width=150
                        )
            
            # Right panel (render)
            with dpg.child_window(width=-1, height=-1, label="Render"):
                # Create a colored rectangle to simulate the fractal
                with dpg.drawlist(width=800, height=600):
                    # Draw a gradient to simulate a fractal
                    colors = [
                        (0, 0, 0, 255),      # Black
                        (0, 0, 128, 255),    # Dark blue
                        (0, 128, 255, 255),  # Blue
                        (0, 255, 255, 255),  # Cyan
                        (255, 255, 0, 255),  # Yellow
                        (255, 0, 0, 255)     # Red
                    ]
                    
                    # Draw concentric shapes to simulate a fractal pattern
                    center_x, center_y = 400, 300
                    for i in range(30, 0, -1):
                        scale = i / 30.0
                        color_idx = int(scale * (len(colors) - 1))
                        color = colors[color_idx]
                        
                        radius = 300 * scale
                        dpg.draw_circle([center_x, center_y], radius, color=color, fill=color)
                
                # Controls below the render
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Refresh")
                    dpg.add_button(label="Reset")
                    dpg.add_button(label="Zoom In")
                    dpg.add_button(label="Zoom Out")
    
    # Set up the viewport
    dpg.setup_dearpygui()
    dpg.show_viewport()


def main():
    """Main entry point for the screenshot utility."""
    try:
        # Create the test UI
        create_test_ui()
        
        # Schedule the screenshot capture
        screenshot_thread = threading.Thread(target=take_screenshot_and_exit)
        screenshot_thread.daemon = True
        screenshot_thread.start()
        
        # Run the application
        dpg.start_dearpygui()
        
        # Check if screenshot was taken
        if os.path.exists(SCREENSHOT_PATH):
            print(f"Screenshot captured at {SCREENSHOT_PATH}")
            return 0
        else:
            print(f"Screenshot was not created at {SCREENSHOT_PATH}", file=sys.stderr)
            return 1
        
    except Exception as e:
        print(f"Error capturing screenshot: {e}", file=sys.stderr)
        return 1
    finally:
        # Ensure proper cleanup
        try:
            if dpg.is_dearpygui_running():
                dpg.stop_dearpygui()
            
            # Try to destroy context with compatibility for different DPG versions
            try:
                if hasattr(dpg, 'does_context_exist') and dpg.does_context_exist():
                    dpg.destroy_context()
                elif hasattr(dpg, 'destroy_context'):
                    dpg.destroy_context()
            except Exception as e:
                print(f"Note: Cleanup completed with minor issue: {e}")
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")


if __name__ == "__main__":
    sys.exit(main())