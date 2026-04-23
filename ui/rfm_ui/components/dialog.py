# Modal dialog component for RFM UI
import dearpygui.dearpygui as dpg

class ModalDialog:
    def __init__(self, label="Dialog", width=400, height=200, callback=None):
        self.label = label
        self.width = width
        self.height = height
        self.callback = callback
        self.window_id = None

    def show(self, content_callback=None):
        """Show the modal dialog."""
        # Calculate center position
        viewport_width = dpg.get_viewport_client_width()
        viewport_height = dpg.get_viewport_client_height()
        pos_x = (viewport_width - self.width) // 2
        pos_y = (viewport_height - self.height) // 2

        with dpg.window(label=self.label, modal=True, width=self.width,
                       height=self.height, pos=(pos_x, pos_y), no_move=True):
            self.window_id = dpg.last_item()

            # Call content callback to populate dialog
            if content_callback:
                content_callback(self.window_id)

            # Add close button if no callback provided
            if not self.callback:
                dpg.add_button(label="Close", callback=self.close,
                              parent=self.window_id)

    def close(self):
        """Close the dialog."""
        if self.window_id and dpg.does_item_exist(self.window_id):
            dpg.delete_item(self.window_id)
            self.window_id = None
