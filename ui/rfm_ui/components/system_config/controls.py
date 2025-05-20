"""
Premium UI controls for the System Configuration UI.

This module provides premium UI controls for the System Configuration UI
with consistent styling, animations, and visual effects.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import time
import dearpygui.dearpygui as dpg

from .constants import THEME, STYLE, ANIMATIONS, SPACING, FONT_SIZES
from .theme import get_theme


class PremiumInput:
    """Base class for premium input controls."""
    
    def __init__(
        self, 
        label: str,
        callback: Optional[Callable] = None,
        width: int = -1,
        tooltip: Optional[str] = None,
        parent: Optional[int] = None,
        default_value: Any = None,
        tag: Optional[int] = None,
        disabled: bool = False,
        on_enter: bool = False,
    ):
        """
        Initialize a premium input control.
        
        Args:
            label: Input label
            callback: Callback function for value changes
            width: Input width (-1 for full width)
            tooltip: Optional tooltip text
            parent: Parent container tag
            default_value: Default input value
            tag: Optional tag for the input
            disabled: Whether the input is disabled
            on_enter: Whether to trigger callback only on Enter key
        """
        self.label = label
        self.callback = callback
        self.width = width
        self.tooltip = tooltip
        self.parent = parent
        self.default_value = default_value
        self.tag = tag or dpg.generate_uuid()
        self.disabled = disabled
        self.on_enter = on_enter
        
        self.input_tag = dpg.generate_uuid()
        self.container_tag = dpg.generate_uuid()
        
        self.theme = get_theme()
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        # Override in subclasses
        pass
    
    def get_value(self) -> Any:
        """
        Get the current value.
        
        Returns:
            Current value
        """
        return dpg.get_value(self.input_tag)
    
    def set_value(self, value: Any) -> None:
        """
        Set the current value.
        
        Args:
            value: New value
        """
        dpg.set_value(self.input_tag, value)
    
    def disable(self) -> None:
        """Disable the input."""
        dpg.disable_item(self.input_tag)
        self.disabled = True
    
    def enable(self) -> None:
        """Enable the input."""
        dpg.enable_item(self.input_tag)
        self.disabled = False
    
    def show(self) -> None:
        """Show the input."""
        dpg.show_item(self.container_tag)
    
    def hide(self) -> None:
        """Hide the input."""
        dpg.hide_item(self.container_tag)
    
    def set_error(self, error: bool = True) -> None:
        """
        Set error state.
        
        Args:
            error: Whether to show error styling
        """
        if error:
            self.theme.apply_error_theme(self.input_tag)
        else:
            self.theme.apply_input_theme(self.input_tag)


class PremiumTextInput(PremiumInput):
    """Premium text input control."""
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        with dpg.group(parent=self.parent, tag=self.container_tag, horizontal=False):
            dpg.add_text(self.label)
            dpg.add_input_text(
                default_value=self.default_value or "",
                callback=self.callback if not self.on_enter else None,
                on_enter=self.callback if self.on_enter else None,
                width=self.width,
                tag=self.input_tag,
                enabled=not self.disabled,
            )
            
            # Add tooltip if provided
            if self.tooltip:
                with dpg.tooltip(self.input_tag):
                    dpg.add_text(self.tooltip)
            
            # Apply premium theme
            self.theme.apply_input_theme(self.input_tag)


class PremiumIntInput(PremiumInput):
    """Premium integer input control."""
    
    def __init__(
        self, 
        label: str,
        callback: Optional[Callable] = None,
        width: int = -1,
        tooltip: Optional[str] = None,
        parent: Optional[int] = None,
        default_value: int = 0,
        tag: Optional[int] = None,
        disabled: bool = False,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        step: int = 1,
    ):
        """
        Initialize a premium integer input control.
        
        Args:
            label: Input label
            callback: Callback function for value changes
            width: Input width (-1 for full width)
            tooltip: Optional tooltip text
            parent: Parent container tag
            default_value: Default input value
            tag: Optional tag for the input
            disabled: Whether the input is disabled
            min_value: Minimum value
            max_value: Maximum value
            step: Step size
        """
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        
        super().__init__(
            label=label,
            callback=callback,
            width=width,
            tooltip=tooltip,
            parent=parent,
            default_value=default_value,
            tag=tag,
            disabled=disabled,
        )
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        with dpg.group(parent=self.parent, tag=self.container_tag, horizontal=False):
            dpg.add_text(self.label)
            dpg.add_input_int(
                default_value=self.default_value or 0,
                callback=self.callback,
                width=self.width,
                tag=self.input_tag,
                enabled=not self.disabled,
                min_value=self.min_value,
                max_value=self.max_value,
                step=self.step,
            )
            
            # Add tooltip if provided
            if self.tooltip:
                with dpg.tooltip(self.input_tag):
                    dpg.add_text(self.tooltip)
            
            # Apply premium theme
            self.theme.apply_input_theme(self.input_tag)


class PremiumFloatInput(PremiumInput):
    """Premium float input control."""
    
    def __init__(
        self, 
        label: str,
        callback: Optional[Callable] = None,
        width: int = -1,
        tooltip: Optional[str] = None,
        parent: Optional[int] = None,
        default_value: float = 0.0,
        tag: Optional[int] = None,
        disabled: bool = False,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: float = 0.1,
        format: str = "%.3f",
    ):
        """
        Initialize a premium float input control.
        
        Args:
            label: Input label
            callback: Callback function for value changes
            width: Input width (-1 for full width)
            tooltip: Optional tooltip text
            parent: Parent container tag
            default_value: Default input value
            tag: Optional tag for the input
            disabled: Whether the input is disabled
            min_value: Minimum value
            max_value: Maximum value
            step: Step size
            format: Display format
        """
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.format = format
        
        super().__init__(
            label=label,
            callback=callback,
            width=width,
            tooltip=tooltip,
            parent=parent,
            default_value=default_value,
            tag=tag,
            disabled=disabled,
        )
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        with dpg.group(parent=self.parent, tag=self.container_tag, horizontal=False):
            dpg.add_text(self.label)
            dpg.add_input_float(
                default_value=self.default_value or 0.0,
                callback=self.callback,
                width=self.width,
                tag=self.input_tag,
                enabled=not self.disabled,
                min_value=self.min_value,
                max_value=self.max_value,
                step=self.step,
                format=self.format,
            )
            
            # Add tooltip if provided
            if self.tooltip:
                with dpg.tooltip(self.input_tag):
                    dpg.add_text(self.tooltip)
            
            # Apply premium theme
            self.theme.apply_input_theme(self.input_tag)


class PremiumColorInput(PremiumInput):
    """Premium color input control."""
    
    def __init__(
        self, 
        label: str,
        callback: Optional[Callable] = None,
        width: int = -1,
        tooltip: Optional[str] = None,
        parent: Optional[int] = None,
        default_value: Union[str, List[float]] = "#FFFFFF",
        tag: Optional[int] = None,
        disabled: bool = False,
        alpha: bool = False,
    ):
        """
        Initialize a premium color input control.
        
        Args:
            label: Input label
            callback: Callback function for value changes
            width: Input width (-1 for full width)
            tooltip: Optional tooltip text
            parent: Parent container tag
            default_value: Default color (hex string or RGB[A] list)
            tag: Optional tag for the input
            disabled: Whether the input is disabled
            alpha: Whether to include alpha channel
        """
        self.alpha = alpha
        self.is_hex = isinstance(default_value, str)
        
        # Convert hex to RGB if needed
        if self.is_hex and isinstance(default_value, str):
            try:
                r = int(default_value[1:3], 16) / 255.0
                g = int(default_value[3:5], 16) / 255.0
                b = int(default_value[5:7], 16) / 255.0
                a = 1.0
                if len(default_value) > 7 and self.alpha:
                    a = int(default_value[7:9], 16) / 255.0
                
                default_value = [r, g, b, a] if self.alpha else [r, g, b]
            except (ValueError, IndexError):
                default_value = [1.0, 1.0, 1.0, 1.0] if self.alpha else [1.0, 1.0, 1.0]
        
        super().__init__(
            label=label,
            callback=self._on_color_change,
            width=width,
            tooltip=tooltip,
            parent=parent,
            default_value=default_value,
            tag=tag,
            disabled=disabled,
        )
        
        self.user_callback = callback
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        with dpg.group(parent=self.parent, tag=self.container_tag, horizontal=False):
            dpg.add_text(self.label)
            dpg.add_color_edit(
                default_value=self.default_value,
                callback=self._on_color_change,
                width=self.width,
                tag=self.input_tag,
                enabled=not self.disabled,
                alpha=self.alpha,
            )
            
            # Display hex value
            self.hex_tag = dpg.generate_uuid()
            dpg.add_text("", tag=self.hex_tag)
            
            # Initial update
            self._update_hex_display(self.default_value)
            
            # Add tooltip if provided
            if self.tooltip:
                with dpg.tooltip(self.input_tag):
                    dpg.add_text(self.tooltip)
    
    def _on_color_change(self, sender, app_data) -> None:
        """
        Handle color changes.
        
        Args:
            sender: Sender ID
            app_data: New color value
        """
        # Update hex display
        self._update_hex_display(app_data)
        
        # Call user callback with hex value
        if self.user_callback and self.is_hex:
            hex_value = self._rgb_to_hex(app_data)
            self.user_callback(sender, hex_value)
        elif self.user_callback:
            self.user_callback(sender, app_data)
    
    def _update_hex_display(self, rgb_value: List[float]) -> None:
        """
        Update the hex display.
        
        Args:
            rgb_value: RGB[A] color value
        """
        hex_value = self._rgb_to_hex(rgb_value)
        dpg.set_value(self.hex_tag, hex_value)
    
    def _rgb_to_hex(self, rgb_value: List[float]) -> str:
        """
        Convert RGB[A] to hex.
        
        Args:
            rgb_value: RGB[A] color value
            
        Returns:
            Hex color string
        """
        r = int(rgb_value[0] * 255)
        g = int(rgb_value[1] * 255)
        b = int(rgb_value[2] * 255)
        
        if self.alpha and len(rgb_value) > 3:
            a = int(rgb_value[3] * 255)
            return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def get_value(self) -> Any:
        """
        Get the current value.
        
        Returns:
            Current value (hex string if initialized with hex, RGB[A] list otherwise)
        """
        rgb_value = dpg.get_value(self.input_tag)
        if self.is_hex:
            return self._rgb_to_hex(rgb_value)
        return rgb_value


class PremiumCheckbox(PremiumInput):
    """Premium checkbox control."""
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        with dpg.group(parent=self.parent, tag=self.container_tag, horizontal=True):
            dpg.add_checkbox(
                label=self.label,
                default_value=bool(self.default_value),
                callback=self.callback,
                tag=self.input_tag,
                enabled=not self.disabled,
            )
            
            # Add tooltip if provided
            if self.tooltip:
                with dpg.tooltip(self.input_tag):
                    dpg.add_text(self.tooltip)


class PremiumCombo(PremiumInput):
    """Premium combo box control."""
    
    def __init__(
        self, 
        label: str,
        items: List[str],
        callback: Optional[Callable] = None,
        width: int = -1,
        tooltip: Optional[str] = None,
        parent: Optional[int] = None,
        default_value: str = "",
        tag: Optional[int] = None,
        disabled: bool = False,
    ):
        """
        Initialize a premium combo box control.
        
        Args:
            label: Input label
            items: List of items
            callback: Callback function for value changes
            width: Input width (-1 for full width)
            tooltip: Optional tooltip text
            parent: Parent container tag
            default_value: Default selected item
            tag: Optional tag for the input
            disabled: Whether the input is disabled
        """
        self.items = items
        
        super().__init__(
            label=label,
            callback=callback,
            width=width,
            tooltip=tooltip,
            parent=parent,
            default_value=default_value,
            tag=tag,
            disabled=disabled,
        )
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        with dpg.group(parent=self.parent, tag=self.container_tag, horizontal=False):
            dpg.add_text(self.label)
            dpg.add_combo(
                items=self.items,
                default_value=self.default_value,
                callback=self.callback,
                width=self.width,
                tag=self.input_tag,
                enabled=not self.disabled,
            )
            
            # Add tooltip if provided
            if self.tooltip:
                with dpg.tooltip(self.input_tag):
                    dpg.add_text(self.tooltip)
            
            # Apply premium theme
            self.theme.apply_input_theme(self.input_tag)


class PremiumButton:
    """Premium button control."""
    
    def __init__(
        self,
        label: str,
        callback: Optional[Callable] = None,
        width: int = -1,
        height: int = 0,
        tooltip: Optional[str] = None,
        parent: Optional[int] = None,
        tag: Optional[int] = None,
        disabled: bool = False,
        primary: bool = True,
        icon: Optional[str] = None,
        small: bool = False,
    ):
        """
        Initialize a premium button.
        
        Args:
            label: Button label
            callback: Callback function
            width: Button width (-1 for full width)
            height: Button height (0 for auto)
            tooltip: Optional tooltip text
            parent: Parent container tag
            tag: Optional tag for the button
            disabled: Whether the button is disabled
            primary: Whether this is a primary button
            icon: Optional icon name
            small: Whether this is a small button
        """
        self.label = label
        self.callback = callback
        self.width = width
        self.height = height
        self.tooltip = tooltip
        self.parent = parent
        self.tag = tag or dpg.generate_uuid()
        self.disabled = disabled
        self.primary = primary
        self.icon = icon
        self.small = small
        
        self.theme = get_theme()
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create the UI for this button."""
        # Create the button
        label_text = self.label
        if self.icon:
            label_text = f"{self.icon} {label_text}"
            
        dpg.add_button(
            label=label_text,
            callback=self.callback,
            width=self.width,
            height=self.height,
            tag=self.tag,
            enabled=not self.disabled,
            parent=self.parent,
        )
        
        # Add tooltip if provided
        if self.tooltip:
            with dpg.tooltip(self.tag):
                dpg.add_text(self.tooltip)
        
        # Apply premium theme
        if self.primary:
            self.theme.apply_button_theme(self.tag)
    
    def disable(self) -> None:
        """Disable the button."""
        dpg.disable_item(self.tag)
        self.disabled = True
    
    def enable(self) -> None:
        """Enable the button."""
        dpg.enable_item(self.tag)
        self.disabled = False
    
    def show(self) -> None:
        """Show the button."""
        dpg.show_item(self.tag)
    
    def hide(self) -> None:
        """Hide the button."""
        dpg.hide_item(self.tag)
    
    def set_label(self, label: str) -> None:
        """
        Set the button label.
        
        Args:
            label: New label
        """
        label_text = label
        if self.icon:
            label_text = f"{self.icon} {label_text}"
            
        dpg.set_item_label(self.tag, label_text)


class PremiumToggle(PremiumInput):
    """Premium toggle control."""
    
    def _create_ui(self) -> None:
        """Create the UI for this control."""
        with dpg.group(parent=self.parent, tag=self.container_tag, horizontal=True):
            dpg.add_text(self.label)
            
            # Create toggle using a selectable
            dpg.add_selectable(
                default_value=bool(self.default_value),
                span_columns=False,
                callback=self.callback,
                tag=self.input_tag,
                enabled=not self.disabled,
                label="  " if bool(self.default_value) else "○",
            )
            
            # Add tooltip if provided
            if self.tooltip:
                with dpg.tooltip(self.input_tag):
                    dpg.add_text(self.tooltip)
            
            # Add custom callback to update the label
            if self.callback:
                original_callback = self.callback
                
                def toggle_callback(sender, app_data):
                    # Update the label
                    dpg.set_item_label(sender, "  " if app_data else "○")
                    # Call the original callback
                    original_callback(sender, app_data)
                
                dpg.set_item_callback(self.input_tag, toggle_callback)
    
    def set_value(self, value: bool) -> None:
        """
        Set the toggle value.
        
        Args:
            value: New value
        """
        dpg.set_value(self.input_tag, value)
        dpg.set_item_label(self.input_tag, "  " if value else "○")


class PremiumFieldEditor:
    """Premium field editor for a configuration value."""
    
    def __init__(
        self,
        key: str,
        path: str,
        value: Any,
        field_type: str,
        parent_tag: int,
        on_change: Callable[[str, Any], None],
        description: Optional[str] = None,
        required: bool = False,
        constraints: Optional[Dict[str, Any]] = None,
        error: bool = False,
    ):
        """
        Initialize a configuration field editor.
        
        Args:
            key: Field key
            path: Full path to the field in the configuration
            value: Current field value
            field_type: Type of the field
            parent_tag: Tag of the parent UI element
            on_change: Callback for value changes
            description: Optional field description
            required: Whether the field is required
            constraints: Optional field constraints
            error: Whether the field has an error
        """
        self.key = key
        self.path = path
        self.value = value
        self.field_type = field_type
        self.parent_tag = parent_tag
        self.on_change = on_change
        self.description = description or ""
        self.required = required
        self.constraints = constraints or {}
        self.error = error
        
        self.tag = dpg.generate_uuid()
        self.input_tag = dpg.generate_uuid()
        self.input_control = None
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create the UI for this field."""
        with dpg.group(parent=self.parent_tag, tag=self.tag, horizontal=False):
            # Field label
            label_text = f"{self.key}"
            if self.required:
                label_text += " *"
            
            with dpg.group(horizontal=True):
                dpg.add_text(label_text)
                
                # Add info icon if we have a description
                if self.description:
                    info_tag = dpg.generate_uuid()
                    dpg.add_text(
                        default_value="(?)",
                        tag=info_tag,
                        color=THEME["info"],
                    )
                    with dpg.tooltip(info_tag):
                        dpg.add_text(self.description)
            
            # Create the appropriate input control based on field type
            if self.field_type == "string":
                self.input_control = PremiumTextInput(
                    label="",
                    default_value=str(self.value) if self.value is not None else "",
                    callback=self._on_text_change,
                    width=-1,
                    parent=self.tag,
                    tag=self.input_tag,
                )
            
            elif self.field_type == "int":
                min_val = self.constraints.get("min")
                max_val = self.constraints.get("max")
                self.input_control = PremiumIntInput(
                    label="",
                    default_value=int(self.value) if self.value is not None else 0,
                    callback=self._on_int_change,
                    width=-1,
                    parent=self.tag,
                    tag=self.input_tag,
                    min_value=min_val,
                    max_value=max_val,
                )
            
            elif self.field_type == "float":
                min_val = self.constraints.get("min")
                max_val = self.constraints.get("max")
                self.input_control = PremiumFloatInput(
                    label="",
                    default_value=float(self.value) if self.value is not None else 0.0,
                    callback=self._on_float_change,
                    width=-1,
                    parent=self.tag,
                    tag=self.input_tag,
                    min_value=min_val,
                    max_value=max_val,
                )
            
            elif self.field_type == "bool":
                self.input_control = PremiumCheckbox(
                    label="",
                    default_value=bool(self.value) if self.value is not None else False,
                    callback=self._on_bool_change,
                    parent=self.tag,
                    tag=self.input_tag,
                )
            
            elif self.field_type == "array":
                # For arrays, we'll just show a text representation for now
                self.input_control = PremiumTextInput(
                    label="",
                    default_value=str(self.value) if self.value is not None else "[]",
                    callback=self._on_array_change,
                    width=-1,
                    parent=self.tag,
                    tag=self.input_tag,
                )
            
            elif self.field_type == "object":
                # For objects, we'll just show a text representation for now
                self.input_control = PremiumTextInput(
                    label="",
                    default_value=str(self.value) if self.value is not None else "{}",
                    width=-1,
                    parent=self.tag,
                    tag=self.input_tag,
                    disabled=True,
                )
                
                # Add a button to open the object editor
                self.edit_button = PremiumButton(
                    label="Edit...",
                    callback=self._on_edit_object,
                    width=-1,
                    parent=self.tag,
                    primary=True,
                )
            
            elif self.field_type == "color":
                # Handle color fields (expected to be hex strings like "#FF0000")
                self.input_control = PremiumColorInput(
                    label="",
                    default_value=self.value if self.value else "#FFFFFF",
                    callback=self._on_color_change,
                    width=-1,
                    parent=self.tag,
                    tag=self.input_tag,
                )
            
            else:
                # Fallback to a text input for unknown types
                self.input_control = PremiumTextInput(
                    label="",
                    default_value=str(self.value) if self.value is not None else "",
                    callback=self._on_text_change,
                    width=-1,
                    parent=self.tag,
                    tag=self.input_tag,
                )
            
            # Add space between fields
            dpg.add_spacer(height=SPACING["sm"], parent=self.tag)
            
            # Set error state if needed
            if self.error:
                self.set_error(True)
    
    def _on_text_change(self, sender, app_data) -> None:
        """Handle text input change."""
        self.value = app_data
        self.on_change(self.path, self.value)
    
    def _on_int_change(self, sender, app_data) -> None:
        """Handle integer input change."""
        self.value = int(app_data)
        self.on_change(self.path, self.value)
    
    def _on_float_change(self, sender, app_data) -> None:
        """Handle float input change."""
        self.value = float(app_data)
        self.on_change(self.path, self.value)
    
    def _on_bool_change(self, sender, app_data) -> None:
        """Handle boolean input change."""
        self.value = bool(app_data)
        self.on_change(self.path, self.value)
    
    def _on_array_change(self, sender, app_data) -> None:
        """Handle array input change."""
        try:
            import ast
            self.value = ast.literal_eval(app_data)
            self.on_change(self.path, self.value)
        except (SyntaxError, ValueError):
            # If invalid, don't update the value
            pass
    
    def _on_object_change(self, sender, app_data) -> None:
        """Handle object input change."""
        try:
            import ast
            self.value = ast.literal_eval(app_data)
            self.on_change(self.path, self.value)
        except (SyntaxError, ValueError):
            # If invalid, don't update the value
            pass
    
    def _on_edit_object(self) -> None:
        """Handle edit object button click."""
        # This should be overridden by the parent to open a nested editor
        pass
    
    def _on_color_change(self, sender, app_data) -> None:
        """Handle color input change."""
        self.value = app_data
        self.on_change(self.path, self.value)
    
    def update_value(self, value: Any) -> None:
        """
        Update the field value.
        
        Args:
            value: New field value
        """
        self.value = value
        
        if self.input_control:
            self.input_control.set_value(value)
    
    def set_error(self, error: bool = True) -> None:
        """
        Set error state.
        
        Args:
            error: Whether to show error styling
        """
        self.error = error
        
        if self.input_control:
            self.input_control.set_error(error)