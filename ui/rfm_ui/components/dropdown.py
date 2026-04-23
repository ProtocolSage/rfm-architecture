# Premium dropdown component for RFM UI
import dearpygui.dearpygui as dpg

class PremiumDropdown:
    def __init__(self, parent_id=None, label="", items=None, default_value=None,
                 callback=None, width=-1, tag=None):
        self.parent_id = parent_id
        self.label = label
        self.items = items or []
        self.default_value = default_value
        self.callback = callback
        self.width = width
        self.tag = tag or f"dropdown_{dpg.generate_uuid()}"
        self.dropdown_id = None

    def create(self):
        self.dropdown_id = dpg.add_combo(
            label=self.label,
            items=self.items,
            default_value=self.default_value,
            callback=self.callback,
            width=self.width,
            parent=self.parent_id,
            tag=self.tag
        )
        return self.dropdown_id

    def set_value(self, value):
        if self.dropdown_id:
            dpg.set_value(self.dropdown_id, value)

    def get_value(self):
        if self.dropdown_id:
            return dpg.get_value(self.dropdown_id)
        return None
