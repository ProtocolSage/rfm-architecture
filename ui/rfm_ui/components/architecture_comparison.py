"""
Architecture Comparison UI components for RFM Architecture.

This module provides UI components for comparing different
architecture configurations and their performance metrics.
"""

import os
import sys
import uuid
import time
import logging
import json
from typing import Dict, List, Tuple, Optional, Set, Any, Callable, Union
import math
import random

import dearpygui.dearpygui as dpg
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

from rfm_ui.theme import Colors, Spacing, Motion
from rfm_ui.components.panel import GlassPanel, CardPanel
from rfm_ui.errors import error_boundary

from rfm.core.node_system_base import (
    Node, Connection, Architecture, 
    NodeType, ConnectionType, EmotionalState,
    calculate_network_metrics, clone_architecture
)
from rfm.core.node_graph import NodeGraph

logger = logging.getLogger(__name__)


class ArchitectureConfig:
    """Container for architecture configuration."""
    
    def __init__(self, 
                architecture: Architecture,
                name: Optional[str] = None,
                description: Optional[str] = None,
                config_id: Optional[str] = None):
        """
        Initialize an architecture configuration.
        
        Args:
            architecture: The architecture
            name: Optional name for the configuration
            description: Optional description
            config_id: Optional unique ID
        """
        self.architecture = architecture
        self.name = name or architecture.name
        self.description = description or architecture.description
        self.id = config_id or str(uuid.uuid4())
        self.metrics = calculate_network_metrics(architecture)
        self.additional_metrics: Dict[str, float] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "id": self.id,
            "architecture": self.architecture.to_dict(),
            "metrics": self.metrics,
            "additional_metrics": self.additional_metrics
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchitectureConfig':
        """Create from dictionary."""
        # Extract architecture
        arch_data = data.get("architecture", {})
        architecture = Architecture.from_dict(arch_data)
        
        # Create instance
        config = cls(
            architecture=architecture,
            name=data.get("name", "Unnamed Config"),
            description=data.get("description", ""),
            config_id=data.get("id")
        )
        
        # Set metrics
        config.metrics = data.get("metrics", {})
        config.additional_metrics = data.get("additional_metrics", {})
        
        return config
        
    def recalculate_metrics(self) -> None:
        """Recalculate metrics for the architecture."""
        self.metrics = calculate_network_metrics(self.architecture)


class ArchitectureComparison:
    """
    Component for comparing different architecture configurations.
    
    This component allows the user to load, compare, and analyze
    multiple architecture configurations side-by-side.
    """
    
    def __init__(self, 
                parent_id: int,
                width: int = -1,
                height: int = -1,
                tag: Optional[str] = None):
        """
        Initialize the architecture comparison component.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            width: Width of the component
            height: Height of the component
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.width = width
        self.height = height
        self.tag = tag or f"arch_compare_{uuid.uuid4()}"
        
        # Comparison state
        self.configurations: List[ArchitectureConfig] = []
        self.selected_configs: Set[str] = set()  # Set of selected config IDs
        self.metric_options: List[str] = []
        self.selected_metric: Optional[str] = None
        
        # UI components
        self.panel: Optional[CardPanel] = None
        self.container_id: Optional[int] = None
        self.config_table_id: Optional[int] = None
        self.chart_texture_id: Optional[str] = None
        self.chart_image_id: Optional[int] = None
        
        # Chart dimensions
        self.chart_width = 600
        self.chart_height = 400
        
        # Create the panel
        self._create_panel()
        
        # Initialize metric options
        self._initialize_metric_options()
        
    def _create_panel(self) -> None:
        """Create the comparison panel."""
        # Create a card panel for the comparison
        self.panel = CardPanel(
            parent_id=self.parent_id,
            label="Architecture Comparison",
            width=self.width,
            height=self.height,
            show_title_bar=True,
            tag=self.tag
        )
        
        # Get panel ID
        panel_id = self.panel.get_panel_id()
        
        # Create the comparison UI
        with dpg.group(parent=panel_id, horizontal=False) as self.container_id:
            # Add toolbar
            with dpg.group(horizontal=True):
                # Add configuration button
                dpg.add_button(
                    label="Add Config",
                    callback=self._on_add_config_clicked,
                    width=100
                )
                
                # Remove configuration button
                dpg.add_button(
                    label="Remove Config",
                    callback=self._on_remove_config_clicked,
                    width=120
                )
                
                # Comparison metric selector
                dpg.add_combo(
                    label="Compare by",
                    items=self.metric_options,
                    width=150,
                    callback=self._on_metric_selected
                )
                
                # Export comparison button
                dpg.add_button(
                    label="Export",
                    callback=self._on_export_clicked,
                    width=80
                )
                
            # Add separator
            dpg.add_separator()
            
            # Create two-row layout
            with dpg.group(horizontal=False):
                # Top row: Configuration table
                with dpg.child_window(width=-1, height=200):
                    with dpg.table(
                        header_row=True,
                        borders_innerH=True,
                        borders_outerH=True,
                        borders_innerV=True,
                        borders_outerV=True,
                        resizable=True,
                        policy=dpg.mvTable_SizingStretchProp,
                        tag=f"{self.tag}_config_table"
                    ) as self.config_table_id:
                        # Add columns
                        dpg.add_table_column(label="Select")
                        dpg.add_table_column(label="Name")
                        dpg.add_table_column(label="Description")
                        dpg.add_table_column(label="Nodes")
                        dpg.add_table_column(label="Connections")
                        dpg.add_table_column(label="Density")
                        dpg.add_table_column(label="Avg Degree")
                
                # Bottom row: Chart and details
                with dpg.group(horizontal=True):
                    # Left side: Chart
                    with dpg.child_window(width=self.chart_width, height=self.chart_height):
                        # Create chart texture
                        with dpg.texture_registry():
                            self.chart_texture_id = f"{self.tag}_chart_texture"
                            dpg.add_raw_texture(
                                self.chart_width, self.chart_height, 
                                np.zeros((self.chart_height, self.chart_width, 4), dtype=np.float32),
                                format=dpg.mvFormat_Float_rgba,
                                tag=self.chart_texture_id
                            )
                            
                        # Add chart image
                        self.chart_image_id = dpg.add_image(
                            self.chart_texture_id, 
                            width=self.chart_width, 
                            height=self.chart_height
                        )
                    
                    # Right side: Details
                    with dpg.child_window(width=-1, height=self.chart_height):
                        dpg.add_text(
                            "Select configurations to compare",
                            tag=f"{self.tag}_details_text"
                        )
            
    def _initialize_metric_options(self) -> None:
        """Initialize the metric options."""
        # Basic metrics (always available)
        self.metric_options = [
            "node_count",
            "connection_count",
            "density",
            "average_degree",
            "connectivity_ratio"
        ]
        
        # Update UI
        if dpg.does_item_exist(f"{self.tag}_metric_combo"):
            dpg.configure_item(
                f"{self.tag}_metric_combo",
                items=self.metric_options
            )
            
        # Set default selected metric
        if self.metric_options:
            self.selected_metric = self.metric_options[0]
            
    def _update_config_table(self) -> None:
        """Update the configuration table with current data."""
        if not self.config_table_id or not dpg.does_item_exist(self.config_table_id):
            return
            
        # Clear existing rows
        for child in dpg.get_item_children(self.config_table_id, 1):
            dpg.delete_item(child)
            
        # Add rows for each configuration
        for config in self.configurations:
            with dpg.table_row(parent=self.config_table_id):
                # Select checkbox
                dpg.add_checkbox(
                    default_value=config.id in self.selected_configs,
                    callback=self._on_config_selected,
                    user_data=config.id
                )
                
                # Name
                dpg.add_text(config.name)
                
                # Description
                dpg.add_text(config.description)
                
                # Nodes
                node_count = config.metrics.get("node_count", 0)
                dpg.add_text(f"{node_count}")
                
                # Connections
                connection_count = config.metrics.get("connection_count", 0)
                dpg.add_text(f"{connection_count}")
                
                # Density
                density = config.metrics.get("density", 0)
                dpg.add_text(f"{density:.3f}")
                
                # Average Degree
                avg_degree = config.metrics.get("average_degree", 0)
                dpg.add_text(f"{avg_degree:.3f}")
                
    def _update_comparison_chart(self) -> None:
        """Update the comparison chart based on selected configs."""
        # Skip if no configs selected
        if not self.selected_configs or not self.selected_metric:
            # Clear chart
            dpg.set_value(
                self.chart_texture_id, 
                np.zeros((self.chart_height, self.chart_width, 4), dtype=np.float32)
            )
            return
            
        # Get selected configurations
        selected_configs = [
            config for config in self.configurations
            if config.id in self.selected_configs
        ]
        
        # Create figure
        fig = plt.figure(figsize=(self.chart_width / 100, self.chart_height / 100), dpi=100, facecolor='#0a0d16')
        ax = fig.add_subplot(111)
        
        # Create bar chart of selected metric
        labels = [config.name for config in selected_configs]
        values = [
            config.metrics.get(self.selected_metric, 0)
            for config in selected_configs
        ]
        
        # Define colors for bars
        colors = [
            Colors.ACCENT,
            Colors.WARNING,
            Colors.SUCCESS,
            Colors.ERROR,
            Colors.TEXT_PRIMARY
        ]
        
        # Plot bars
        bars = ax.bar(
            range(len(labels)), 
            values, 
            color=[colors[i % len(colors)] for i in range(len(labels))]
        )
        
        # Add labels
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", color="white")
        ax.tick_params(axis='y', colors='white')
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}',
                    ha='center', va='bottom', color="white", fontsize=8)
                    
        # Set title and ylabel
        ax.set_title(f"Comparison by {self.selected_metric}", color="white")
        ax.set_ylabel(self.selected_metric, color="white")
        
        # Set facecolor
        ax.set_facecolor('#0a0d16')
        
        # Convert figure to numpy array
        fig.tight_layout(pad=0.5)
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        
        # Get RGBA buffer
        buf = canvas.buffer_rgba()
        image_array = np.asarray(buf)
        
        # Convert to float32 normalized array (0-1)
        image_array = image_array.astype(np.float32) / 255.0
        
        # Update texture
        dpg.set_value(self.chart_texture_id, image_array)
        
        # Close figure
        plt.close(fig)
        
    def _update_details_text(self) -> None:
        """Update the details text for selected configurations."""
        # Get selected configurations
        selected_configs = [
            config for config in self.configurations
            if config.id in self.selected_configs
        ]
        
        if not selected_configs:
            # No configs selected
            dpg.set_value(f"{self.tag}_details_text", "Select configurations to compare")
            return
            
        # Build details text
        details = "Configuration Details:\n\n"
        
        for config in selected_configs:
            details += f"=== {config.name} ===\n"
            
            if config.description:
                details += f"Description: {config.description}\n"
                
            details += f"Nodes: {config.metrics.get('node_count', 0)}\n"
            details += f"Connections: {config.metrics.get('connection_count', 0)}\n"
            details += f"Density: {config.metrics.get('density', 0):.3f}\n"
            details += f"Average Degree: {config.metrics.get('average_degree', 0):.3f}\n"
            details += f"Connectivity Ratio: {config.metrics.get('connectivity_ratio', 0):.3f}\n"
            
            # Add additional metrics if available
            for metric_name, metric_value in config.additional_metrics.items():
                if isinstance(metric_value, float):
                    details += f"{metric_name}: {metric_value:.3f}\n"
                else:
                    details += f"{metric_name}: {metric_value}\n"
                    
            details += "\n"
            
        # Add comparison summary if multiple configs selected
        if len(selected_configs) > 1 and self.selected_metric:
            details += "=== Comparison Summary ===\n"
            details += f"Comparing by: {self.selected_metric}\n"
            
            # Find best value
            values = [
                (config.name, config.metrics.get(self.selected_metric, 0))
                for config in selected_configs
            ]
            
            best_name, best_value = max(values, key=lambda x: x[1])
            details += f"Highest value: {best_name} ({best_value:.3f})\n"
            
        # Update details text
        dpg.set_value(f"{self.tag}_details_text", details)
        
    @error_boundary
    def _on_add_config_clicked(self, sender, app_data) -> None:
        """Handle add configuration button click."""
        # Show dialog for adding a configuration
        with dpg.window(label="Add Configuration", modal=True, width=500, height=300, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Select a method to add a configuration:")
            
            # Add tabs for different methods
            with dpg.tab_bar():
                # Tab for loading from file
                with dpg.tab(label="Load from File"):
                    file_tab_id = dpg.last_item()
                    
                    dpg.add_text("Enter the filepath to load:", parent=file_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_load_filepath",
                        width=-1,
                        hint="architecture.json",
                        parent=file_tab_id
                    )
                    
                    dpg.add_button(
                        label="Load",
                        callback=self._load_configuration_from_file,
                        user_data=dialog_id,
                        width=100,
                        parent=file_tab_id
                    )
                    
                # Tab for creating from template
                with dpg.tab(label="Create from Template"):
                    template_tab_id = dpg.last_item()
                    
                    dpg.add_text("Select a template:", parent=template_tab_id)
                    dpg.add_combo(
                        items=["Default Architecture", "RFM Architecture", "Empty Architecture"],
                        default_value="Default Architecture",
                        width=-1,
                        tag=f"{self.tag}_template_combo",
                        parent=template_tab_id
                    )
                    
                    dpg.add_text("Configuration Name:", parent=template_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_template_name",
                        width=-1,
                        default_value="New Configuration",
                        parent=template_tab_id
                    )
                    
                    dpg.add_text("Description:", parent=template_tab_id)
                    dpg.add_input_text(
                        tag=f"{self.tag}_template_description",
                        width=-1,
                        multiline=True,
                        height=80,
                        parent=template_tab_id
                    )
                    
                    dpg.add_button(
                        label="Create",
                        callback=self._create_configuration_from_template,
                        user_data=dialog_id,
                        width=100,
                        parent=template_tab_id
                    )
                    
            # Cancel button
            dpg.add_button(
                label="Cancel",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=dialog_id,
                width=100
            )
            
    def _load_configuration_from_file(self, sender, app_data, user_data) -> None:
        """Load a configuration from file."""
        # Get filepath
        filepath = dpg.get_value(f"{self.tag}_load_filepath")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        try:
            # Load architecture from file
            architecture = Architecture.load_from_file(filepath)
            
            if architecture:
                # Create configuration
                config = ArchitectureConfig(
                    architecture=architecture,
                    name=architecture.name or os.path.basename(filepath),
                    description=architecture.description or f"Loaded from {filepath}"
                )
                
                # Add to configurations
                self.configurations.append(config)
                
                # Update UI
                self._update_config_table()
                
                # Show success message
                with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
                    result_id = dpg.last_item()
                    
                    dpg.add_text(f"Successfully loaded from {filepath}")
                    dpg.add_button(
                        label="OK",
                        callback=lambda s, a, u: dpg.delete_item(u),
                        user_data=result_id,
                        width=100
                    )
            else:
                # Show error message
                with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                    result_id = dpg.last_item()
                    
                    dpg.add_text(f"Failed to load from {filepath}")
                    dpg.add_button(
                        label="OK",
                        callback=lambda s, a, u: dpg.delete_item(u),
                        user_data=result_id,
                        width=100
                    )
        except Exception as e:
            # Show error message
            with dpg.window(label="Error", modal=True, width=400, height=150, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Error loading configuration: {str(e)}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
                
    def _create_configuration_from_template(self, sender, app_data, user_data) -> None:
        """Create a configuration from template."""
        # Get template
        template = dpg.get_value(f"{self.tag}_template_combo")
        
        # Get name and description
        name = dpg.get_value(f"{self.tag}_template_name")
        description = dpg.get_value(f"{self.tag}_template_description")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Create architecture from template
        from rfm.core.node_system_base import create_default_architecture, create_rfm_architecture
        
        if template == "Default Architecture":
            architecture = create_default_architecture()
        elif template == "RFM Architecture":
            architecture = create_rfm_architecture()
        else:  # Empty Architecture
            architecture = Architecture()
            
        # Set name and description if provided
        if name:
            architecture.name = name
            
        if description:
            architecture.description = description
            
        # Create configuration
        config = ArchitectureConfig(
            architecture=architecture,
            name=name or template,
            description=description or f"Created from {template} template"
        )
        
        # Add to configurations
        self.configurations.append(config)
        
        # Update UI
        self._update_config_table()
        
    @error_boundary
    def _on_remove_config_clicked(self, sender, app_data) -> None:
        """Handle remove configuration button click."""
        # Check if any configs are selected
        if not self.selected_configs:
            # Show error message
            with dpg.window(label="Error", modal=True, width=300, height=100, pos=(400, 200)):
                dpg.add_text("No configurations selected")
                dpg.add_button(
                    label="OK",
                    callback=lambda: dpg.delete_item(dpg.last_container()),
                    width=100
                )
                
            return
            
        # Show confirmation dialog
        with dpg.window(label="Remove Configurations", modal=True, width=300, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text(f"Remove {len(self.selected_configs)} selected configuration(s)?")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._remove_selected_configurations,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _remove_selected_configurations(self, sender, app_data, user_data) -> None:
        """Remove selected configurations."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Remove selected configurations
        self.configurations = [
            config for config in self.configurations
            if config.id not in self.selected_configs
        ]
        
        # Clear selection
        self.selected_configs.clear()
        
        # Update UI
        self._update_config_table()
        self._update_comparison_chart()
        self._update_details_text()
        
    @error_boundary
    def _on_config_selected(self, sender, app_data, user_data) -> None:
        """Handle config selection checkbox."""
        # Get config ID from user_data
        config_id = user_data
        
        # Update selected configs set
        if app_data:
            self.selected_configs.add(config_id)
        else:
            self.selected_configs.discard(config_id)
            
        # Update chart and details
        self._update_comparison_chart()
        self._update_details_text()
        
    @error_boundary
    def _on_metric_selected(self, sender, app_data) -> None:
        """Handle metric selection."""
        self.selected_metric = app_data
        
        # Update chart
        self._update_comparison_chart()
        self._update_details_text()
        
    @error_boundary
    def _on_export_clicked(self, sender, app_data) -> None:
        """Handle export button click."""
        # Show export options dialog
        with dpg.window(label="Export Comparison", modal=True, width=400, height=200, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Export Options")
            
            # Option 1: Export selected configs
            dpg.add_checkbox(
                label="Export selected configurations",
                default_value=True,
                tag=f"{self.tag}_export_selected"
            )
            
            # Option 2: Export chart
            dpg.add_checkbox(
                label="Export comparison chart",
                default_value=True,
                tag=f"{self.tag}_export_chart"
            )
            
            # Filepath
            dpg.add_text("Export to file:")
            dpg.add_input_text(
                tag=f"{self.tag}_export_filepath",
                width=-1,
                default_value="architecture_comparison.json"
            )
            
            # Export chart filepath
            dpg.add_text("Export chart to file:")
            dpg.add_input_text(
                tag=f"{self.tag}_export_chart_filepath",
                width=-1,
                default_value="comparison_chart.png"
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Export",
                    callback=self._export_comparison,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _export_comparison(self, sender, app_data, user_data) -> None:
        """Export the comparison."""
        # Get export options
        export_selected = dpg.get_value(f"{self.tag}_export_selected")
        export_chart = dpg.get_value(f"{self.tag}_export_chart")
        filepath = dpg.get_value(f"{self.tag}_export_filepath")
        chart_filepath = dpg.get_value(f"{self.tag}_export_chart_filepath")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        # Export selected configurations
        success = True
        message = ""
        
        if export_selected:
            try:
                # Get configs to export
                if self.selected_configs:
                    configs_to_export = [
                        config for config in self.configurations
                        if config.id in self.selected_configs
                    ]
                else:
                    configs_to_export = self.configurations
                    
                # Convert to dict
                configs_data = [config.to_dict() for config in configs_to_export]
                
                # Save to file
                with open(filepath, 'w') as f:
                    json.dump(configs_data, f, indent=2)
                    
                message += f"Successfully exported configurations to {filepath}\n"
            except Exception as e:
                success = False
                message += f"Error exporting configurations: {str(e)}\n"
                
        # Export chart
        if export_chart and self.selected_metric and self.selected_configs:
            try:
                # Create figure for export
                # Same as _update_comparison_chart but higher quality
                
                # Get selected configurations
                selected_configs = [
                    config for config in self.configurations
                    if config.id in self.selected_configs
                ]
                
                # Create figure (higher dpi for export)
                fig = plt.figure(figsize=(10, 8), dpi=300, facecolor='#0a0d16')
                ax = fig.add_subplot(111)
                
                # Create bar chart of selected metric
                labels = [config.name for config in selected_configs]
                values = [
                    config.metrics.get(self.selected_metric, 0)
                    for config in selected_configs
                ]
                
                # Define colors for bars
                colors = [
                    Colors.ACCENT,
                    Colors.WARNING,
                    Colors.SUCCESS,
                    Colors.ERROR,
                    Colors.TEXT_PRIMARY
                ]
                
                # Plot bars
                bars = ax.bar(
                    range(len(labels)), 
                    values, 
                    color=[colors[i % len(colors)] for i in range(len(labels))]
                )
                
                # Add labels
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=45, ha="right", color="white")
                ax.tick_params(axis='y', colors='white")
                
                # Add values on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                            f'{height:.3f}",
                            ha='center', va='bottom', color="white", fontsize=10)
                            
                # Set title and ylabel
                ax.set_title(f"Comparison by {self.selected_metric}", color="white")
                ax.set_ylabel(self.selected_metric, color="white")
                
                # Set facecolor
                ax.set_facecolor('#0a0d16')
                
                # Save figure
                fig.tight_layout(pad=0.5)
                plt.savefig(chart_filepath, dpi=300, facecolor='#0a0d16')
                plt.close(fig)
                
                message += f"Successfully exported chart to {chart_filepath}\n"
            except Exception as e:
                success = False
                message += f"Error exporting chart: {str(e)}\n"
                
        # Show result message
        if success:
            with dpg.window(label="Export Complete", modal=True, width=400, height=150, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(message)
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
        else:
            with dpg.window(label="Export Error", modal=True, width=400, height=150, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(message)
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
                
    def add_configuration(self, config: ArchitectureConfig) -> None:
        """
        Add a configuration to compare.
        
        Args:
            config: Configuration to add
        """
        self.configurations.append(config)
        
        # Update UI
        self._update_config_table()
        
    def import_configurations(self, filepath: str) -> bool:
        """
        Import configurations from file.
        
        Args:
            filepath: Path to configurations file
            
        Returns:
            True if import was successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                configs_data = json.load(f)
                
            # Convert to configurations
            configs = [ArchitectureConfig.from_dict(data) for data in configs_data]
            
            # Add to configurations
            self.configurations.extend(configs)
            
            # Update UI
            self._update_config_table()
            
            return True
        except Exception as e:
            logger.error(f"Error importing configurations: {e}")
            return False
            
    def clear_configurations(self) -> None:
        """Clear all configurations."""
        self.configurations.clear()
        self.selected_configs.clear()
        
        # Update UI
        self._update_config_table()
        self._update_comparison_chart()
        self._update_details_text()