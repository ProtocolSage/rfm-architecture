# Preview canvas component for RFM UI
import dearpygui.dearpygui as dpg

class PreviewCanvas:
    def __init__(self, parent_id=None, width=800, height=600, tag=None):
        self.parent_id = parent_id
        self.width = width
        self.height = height
        self.tag = tag or f"preview_canvas_{dpg.generate_uuid()}"
        self.canvas_id = None

    def create(self):
        with dpg.drawlist(parent=self.parent_id, width=self.width, height=self.height, tag=self.tag):
            self.canvas_id = dpg.last_item()
        return self.canvas_id
