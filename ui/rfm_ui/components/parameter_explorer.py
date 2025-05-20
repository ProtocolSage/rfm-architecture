"""
Parameter Explorer UI components for RFM Architecture.

This module provides UI components for exploring and testing
architecture parameters and structural hypotheses.
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

logger = logging.getLogger(__name__)


class ParameterTestResult:
    """Container for parameter test results."""
    
    def __init__(self, 
                name: str,
                parameter_values: Dict[str, Any],
                metrics: Dict[str, float],
                test_id: Optional[str] = None):
        """
        Initialize a test result.
        
        Args:
            name: Test name/description
            parameter_values: Parameter values used for the test
            metrics: Performance metrics from the test
            test_id: Optional unique ID for the test
        """
        self.name = name
        self.parameter_values = parameter_values
        self.metrics = metrics
        self.test_id = test_id or str(uuid.uuid4())
        self.timestamp = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "parameter_values": self.parameter_values,
            "metrics": self.metrics,
            "test_id": self.test_id,
            "timestamp": self.timestamp
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterTestResult':
        """Create from dictionary."""
        return cls(
            name=data.get("name", "Unnamed Test"),
            parameter_values=data.get("parameter_values", {}),
            metrics=data.get("metrics", {}),
            test_id=data.get("test_id")
        )


class ParameterExplorer:
    """
    Explorer component for testing architecture parameters.
    
    This component allows for testing different configurations
    and parameter settings, and comparing their performance.
    """
    
    def __init__(self, 
                parent_id: int,
                architecture: Optional[Architecture] = None,
                on_architecture_change: Optional[Callable[[Architecture], None]] = None,
                width: int = -1,
                height: int = -1,
                tag: Optional[str] = None):
        """
        Initialize the parameter explorer.
        
        Args:
            parent_id: DearPyGui ID of the parent container
            architecture: Optional architecture to explore
            on_architecture_change: Callback for architecture changes
            width: Width of the explorer
            height: Height of the explorer
            tag: Optional tag for the component
        """
        self.parent_id = parent_id
        self.architecture = architecture or Architecture()
        self.on_architecture_change = on_architecture_change
        self.width = width
        self.height = height
        self.tag = tag or f"param_explorer_{uuid.uuid4()}"
        
        # Test state
        self.test_results: List[ParameterTestResult] = []
        self.parameters_to_test: Dict[str, Dict[str, Any]] = {}
        self.selected_result_index: Optional[int] = None
        
        # UI components
        self.panel: Optional[CardPanel] = None
        self.container_id: Optional[int] = None
        self.parameter_list_id: Optional[int] = None
        self.results_list_id: Optional[int] = None
        self.chart_texture_id: Optional[str] = None
        self.chart_image_id: Optional[int] = None
        
        # Chart dimensions
        self.chart_width = 400
        self.chart_height = 300
        
        # Create the panel
        self._create_panel()
        
    def _create_panel(self) -> None:
        """Create the explorer panel."""
        # Create a card panel for the explorer
        self.panel = CardPanel(
            parent_id=self.parent_id,
            label="Parameter Explorer",
            width=self.width,
            height=self.height,
            show_title_bar=True,
            tag=self.tag
        )
        
        # Get panel ID
        panel_id = self.panel.get_panel_id()
        
        # Create the explorer UI
        with dpg.group(parent=panel_id, horizontal=False) as self.container_id:
            # Add toolbar
            with dpg.group(horizontal=True):
                # Run test button
                dpg.add_button(
                    label="Run Test",
                    callback=self._on_run_test_clicked,
                    width=80
                )
                
                # Clear results button
                dpg.add_button(
                    label="Clear Results",
                    callback=self._on_clear_results_clicked,
                    width=100
                )
                
                # Apply result button
                dpg.add_button(
                    label="Apply Selected",
                    callback=self._on_apply_result_clicked,
                    width=120
                )
                
                # Export results button
                dpg.add_button(
                    label="Export Results",
                    callback=self._on_export_clicked,
                    width=120
                )
                
            # Add separator
            dpg.add_separator()
            
            # Create two-column layout
            with dpg.group(horizontal=True):
                # Left column: Parameters and settings
                with dpg.child_window(width=300, height=-1):
                    left_container = dpg.last_item()
                    
                    # Parameter sections
                    with dpg.collapsing_header(label="Node Parameters", default_open=True):
                        # Node density slider
                        dpg.add_text("Node Density")
                        dpg.add_slider_float(
                            tag=f"{self.tag}_node_density",
                            default_value=0.5,
                            min_value=0.1,
                            max_value=1.0,
                            format="%.2f",
                            width=-1,
                            callback=self._on_parameter_changed
                        )
                        
                        # Node type distribution
                        dpg.add_text("Node Type Distribution")
                        with dpg.group(horizontal=True):
                            dpg.add_slider_float(
                                label="Standard",
                                tag=f"{self.tag}_node_type_standard",
                                default_value=0.5,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                            dpg.add_slider_float(
                                label="Processor",
                                tag=f"{self.tag}_node_type_processor",
                                default_value=0.3,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                        
                        with dpg.group(horizontal=True):
                            dpg.add_slider_float(
                                label="Memory",
                                tag=f"{self.tag}_node_type_memory",
                                default_value=0.2,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                            dpg.add_slider_float(
                                label="Other",
                                tag=f"{self.tag}_node_type_other",
                                default_value=0.0,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                            
                    with dpg.collapsing_header(label="Connection Parameters", default_open=True):
                        # Connection density slider
                        dpg.add_text("Connection Density")
                        dpg.add_slider_float(
                            tag=f"{self.tag}_connection_density",
                            default_value=0.3,
                            min_value=0.1,
                            max_value=1.0,
                            format="%.2f",
                            width=-1,
                            callback=self._on_parameter_changed
                        )
                        
                        # Connection type distribution
                        dpg.add_text("Connection Type Distribution")
                        with dpg.group(horizontal=True):
                            dpg.add_slider_float(
                                label="Standard",
                                tag=f"{self.tag}_conn_type_standard",
                                default_value=0.6,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                            dpg.add_slider_float(
                                label="Excitatory",
                                tag=f"{self.tag}_conn_type_excitatory",
                                default_value=0.2,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                        
                        with dpg.group(horizontal=True):
                            dpg.add_slider_float(
                                label="Inhibitory",
                                tag=f"{self.tag}_conn_type_inhibitory",
                                default_value=0.1,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                            dpg.add_slider_float(
                                label="Bidirectional",
                                tag=f"{self.tag}_conn_type_bidirectional",
                                default_value=0.1,
                                min_value=0.0,
                                max_value=1.0,
                                width=100,
                                callback=self._on_parameter_changed
                            )
                            
                    with dpg.collapsing_header(label="Test Settings", default_open=True):
                        # Number of test iterations
                        dpg.add_text("Iterations")
                        dpg.add_slider_int(
                            tag=f"{self.tag}_iterations",
                            default_value=5,
                            min_value=1,
                            max_value=20,
                            width=-1
                        )
                        
                        # Test name
                        dpg.add_text("Test Name")
                        dpg.add_input_text(
                            tag=f"{self.tag}_test_name",
                            default_value="Test Run",
                            width=-1
                        )
                
                # Right column: Results and charts
                with dpg.child_window(width=-1, height=-1):
                    right_container = dpg.last_item()
                    
                    # Results section
                    dpg.add_text("Test Results", parent=right_container)
                    
                    # Results list
                    self.results_list_id = dpg.add_listbox(
                        items=[],
                        width=-1,
                        num_items=5,
                        callback=self._on_result_selected,
                        parent=right_container
                    )
                    
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
                        height=self.chart_height,
                        parent=right_container
                    )
                    
                    # Add result details text
                    dpg.add_text(
                        "Select a result to view details",
                        tag=f"{self.tag}_result_details",
                        parent=right_container
                    )
            
    def _update_parameters_to_test(self) -> None:
        """Update the parameters to test from UI values."""
        self.parameters_to_test = {
            "node_density": {
                "value": dpg.get_value(f"{self.tag}_node_density"),
                "description": "Node Density"
            },
            "node_type_distribution": {
                "standard": dpg.get_value(f"{self.tag}_node_type_standard"),
                "processor": dpg.get_value(f"{self.tag}_node_type_processor"),
                "memory": dpg.get_value(f"{self.tag}_node_type_memory"),
                "other": dpg.get_value(f"{self.tag}_node_type_other"),
                "description": "Node Type Distribution"
            },
            "connection_density": {
                "value": dpg.get_value(f"{self.tag}_connection_density"),
                "description": "Connection Density"
            },
            "connection_type_distribution": {
                "standard": dpg.get_value(f"{self.tag}_conn_type_standard"),
                "excitatory": dpg.get_value(f"{self.tag}_conn_type_excitatory"),
                "inhibitory": dpg.get_value(f"{self.tag}_conn_type_inhibitory"),
                "bidirectional": dpg.get_value(f"{self.tag}_conn_type_bidirectional"),
                "description": "Connection Type Distribution"
            }
        }
        
    def _update_results_list(self) -> None:
        """Update the results list with current test results."""
        if not self.results_list_id or not dpg.does_item_exist(self.results_list_id):
            return
            
        # Get result names
        result_items = []
        for result in self.test_results:
            result_items.append(result.name)
            
        # Update listbox
        dpg.configure_item(self.results_list_id, items=result_items)
        
    def _update_result_details(self) -> None:
        """Update the result details display for the selected result."""
        if self.selected_result_index is None or self.selected_result_index >= len(self.test_results):
            return
            
        # Get selected result
        result = self.test_results[self.selected_result_index]
        
        # Format details string
        details = f"Result: {result.name}\n\n"
        details += "Parameters:\n"
        
        for param_name, param_value in result.parameter_values.items():
            if isinstance(param_value, dict) and "description" in param_value:
                # Skip description field
                param_desc = param_value.pop("description", "")
                details += f"- {param_desc}:\n"
                
                for k, v in param_value.items():
                    details += f"  - {k}: {v:.2f if isinstance(v, float) else v}\n"
                    
                # Restore description
                param_value["description"] = param_desc
            else:
                details += f"- {param_name}: {param_value:.2f if isinstance(param_value, float) else param_value}\n"
                
        details += "\nMetrics:\n"
        for metric_name, metric_value in result.metrics.items():
            details += f"- {metric_name}: {metric_value:.4f if isinstance(metric_value, float) else metric_value}\n"
            
        # Update details text
        dpg.set_value(f"{self.tag}_result_details", details)
        
        # Update chart
        self._update_result_chart()
        
    def _update_result_chart(self) -> None:
        """Update the chart for the selected result."""
        if self.selected_result_index is None or self.selected_result_index >= len(self.test_results):
            return
            
        # Get selected result
        result = self.test_results[self.selected_result_index]
        
        # Create figure
        fig = plt.figure(figsize=(self.chart_width / 100, self.chart_height / 100), dpi=100, facecolor='#0a0d16')
        ax = fig.add_subplot(111)
        
        # Extract metrics for chart
        metrics = result.metrics
        
        # Create bar chart of metrics
        labels = []
        values = []
        
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                labels.append(name)
                values.append(value)
                
        # Plot bars
        if labels and values:
            bars = ax.bar(range(len(labels)), values, color=Colors.ACCENT)
            
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
                        
            # Set title
            ax.set_title(result.name, color="white")
            
            # Set facecolor
            ax.set_facecolor('#0a0d16')
        else:
            # No numeric metrics, show text
            ax.text(0.5, 0.5, "No numeric metrics available",
                   ha='center', va='center', color="white")
            ax.set_xticks([])
            ax.set_yticks([])
            
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
        
    @error_boundary
    def _on_parameter_changed(self, sender, app_data) -> None:
        """Handle parameter value change."""
        # Update parameters to test
        self._update_parameters_to_test()
        
    @error_boundary
    def _on_run_test_clicked(self, sender, app_data) -> None:
        """Handle run test button click."""
        # Update parameters to test
        self._update_parameters_to_test()
        
        # Get iterations
        iterations = dpg.get_value(f"{self.tag}_iterations")
        
        # Get test name
        test_name = dpg.get_value(f"{self.tag}_test_name")
        
        # Run test
        self._run_parameter_test(test_name, iterations)
        
    def _run_parameter_test(self, test_name: str, iterations: int) -> None:
        """
        Run a parameter test.
        
        Args:
            test_name: Name for the test
            iterations: Number of test iterations
        """
        # Show progress dialog
        with dpg.window(label="Running Test", modal=True, width=300, height=100, pos=(400, 200)) as progress_window:
            dpg.add_text("Running parameter test...")
            progress_bar = dpg.add_progress_bar(width=-1, default_value=0.0)
            
        # Clone the architecture for testing
        test_arch = clone_architecture(self.architecture)
        
        # Apply parameters to architecture
        metrics = self._apply_parameters_and_measure(test_arch, iterations, progress_bar, progress_window)
        
        # Create test result
        result = ParameterTestResult(
            name=test_name,
            parameter_values=self.parameters_to_test,
            metrics=metrics
        )
        
        # Add to results
        self.test_results.append(result)
        
        # Update UI
        self._update_results_list()
        
        # Select the new result
        self.selected_result_index = len(self.test_results) - 1
        self._update_result_details()
        
        # Close progress dialog
        dpg.delete_item(progress_window)
        
    def _apply_parameters_and_measure(self, 
                                     architecture: Architecture, 
                                     iterations: int,
                                     progress_bar: int,
                                     progress_window: int) -> Dict[str, float]:
        """
        Apply parameters to architecture and measure performance.
        
        Args:
            architecture: Architecture to modify
            iterations: Number of test iterations
            progress_bar: DPG progress bar ID
            progress_window: DPG progress window ID
            
        Returns:
            Dictionary of performance metrics
        """
        # Check if the architecture is empty or has very few nodes
        if len(architecture.nodes) < 3:
            # Create some nodes for testing
            for i in range(10):
                node = Node(
                    id=str(uuid.uuid4()),
                    name=f"Test Node {i+1}",
                    type=NodeType.STANDARD,
                    position=(random.uniform(-1, 1), random.uniform(-1, 1), 0.0),
                    color="#42d7f5",
                    size=1.0
                )
                architecture.add_node(node)
                
        # Collect metrics for each iteration
        all_metrics = []
        
        for i in range(iterations):
            # Update progress
            progress = (i / iterations) * 100
            dpg.set_value(progress_bar, progress / 100.0)
            dpg.set_value(f"{progress_window}_text", f"Running iteration {i+1}/{iterations}...")
            
            # Clone architecture for this iteration
            iter_arch = clone_architecture(architecture)
            
            # Apply node parameters
            self._apply_node_parameters(iter_arch)
            
            # Apply connection parameters
            self._apply_connection_parameters(iter_arch)
            
            # Measure performance
            metrics = calculate_network_metrics(iter_arch)
            all_metrics.append(metrics)
            
            # Process UI events
            dpg.render_dearpygui_frame()
            
        # Calculate average metrics
        final_metrics = {}
        
        for metric_name in all_metrics[0].keys():
            values = [metrics[metric_name] for metrics in all_metrics]
            final_metrics[metric_name] = sum(values) / len(values)
            
            # Add min/max/std
            final_metrics[f"{metric_name}_min"] = min(values)
            final_metrics[f"{metric_name}_max"] = max(values)
            final_metrics[f"{metric_name}_std"] = np.std(values) if len(values) > 1 else 0.0
            
        # Calculate additional metrics
        self._calculate_additional_metrics(final_metrics)
        
        return final_metrics
        
    def _apply_node_parameters(self, architecture: Architecture) -> None:
        """
        Apply node parameters to architecture.
        
        Args:
            architecture: Architecture to modify
        """
        # Get node parameters
        node_density = self.parameters_to_test.get("node_density", {}).get("value", 0.5)
        node_type_dist = self.parameters_to_test.get("node_type_distribution", {})
        
        # Calculate target node count based on density
        target_node_count = int(20 * node_density)  # Scale to reasonable range
        
        # Adjust node count
        current_count = len(architecture.nodes)
        
        if current_count < target_node_count:
            # Add nodes
            for i in range(current_count, target_node_count):
                # Determine node type based on distribution
                node_type = self._select_node_type(node_type_dist)
                
                # Create node
                node = Node(
                    id=str(uuid.uuid4()),
                    name=f"Node {i+1}",
                    type=node_type,
                    position=(random.uniform(-1, 1), random.uniform(-1, 1), 0.0),
                    color=self._get_color_for_type(node_type),
                    size=1.0
                )
                
                architecture.add_node(node)
        elif current_count > target_node_count:
            # Remove nodes
            for _ in range(current_count - target_node_count):
                # Choose a random node to remove
                if architecture.nodes:
                    node_index = random.randint(0, len(architecture.nodes) - 1)
                    node_id = architecture.nodes[node_index].id
                    architecture.remove_node(node_id)
                    
        # Update node types based on distribution
        for node in architecture.nodes:
            # Randomly decide whether to change this node's type
            if random.random() < 0.3:  # 30% chance to change
                node_type = self._select_node_type(node_type_dist)
                architecture.update_node(node.id, {"type": node_type})
                
                # Update color based on type
                color = self._get_color_for_type(node_type)
                architecture.update_node(node.id, {"color": color})
                
    def _select_node_type(self, distribution: Dict[str, Any]) -> NodeType:
        """
        Select a node type based on distribution.
        
        Args:
            distribution: Node type distribution
            
        Returns:
            Selected node type
        """
        # Get distribution values
        standard = distribution.get("standard", 0.5)
        processor = distribution.get("processor", 0.3)
        memory = distribution.get("memory", 0.2)
        other = distribution.get("other", 0.0)
        
        # Normalize
        total = standard + processor + memory + other
        if total <= 0:
            return NodeType.STANDARD
            
        standard /= total
        processor /= total
        memory /= total
        other /= total
        
        # Select type
        r = random.random()
        
        if r < standard:
            return NodeType.STANDARD
        elif r < standard + processor:
            return NodeType.PROCESSOR
        elif r < standard + processor + memory:
            return NodeType.MEMORY
        else:
            # For "other", randomly select from remaining types
            other_types = [
                NodeType.INPUT, 
                NodeType.OUTPUT, 
                NodeType.CONTROLLER, 
                NodeType.ROUTER, 
                NodeType.CUSTOM
            ]
            return random.choice(other_types)
            
    def _get_color_for_type(self, node_type: NodeType) -> str:
        """
        Get a color for a node type.
        
        Args:
            node_type: Node type
            
        Returns:
            Hex color string
        """
        if node_type == NodeType.STANDARD:
            return "#42d7f5"  # Cyan
        elif node_type == NodeType.PROCESSOR:
            return "#f54242"  # Red
        elif node_type == NodeType.MEMORY:
            return "#42f584"  # Green
        elif node_type == NodeType.INPUT:
            return "#4287f5"  # Blue
        elif node_type == NodeType.OUTPUT:
            return "#f5a742"  # Orange
        elif node_type == NodeType.CONTROLLER:
            return "#9942f5"  # Purple
        elif node_type == NodeType.ROUTER:
            return "#f542e3"  # Pink
        else:
            return "#ffffff"  # White
            
    def _apply_connection_parameters(self, architecture: Architecture) -> None:
        """
        Apply connection parameters to architecture.
        
        Args:
            architecture: Architecture to modify
        """
        # Get connection parameters
        connection_density = self.parameters_to_test.get("connection_density", {}).get("value", 0.3)
        connection_type_dist = self.parameters_to_test.get("connection_type_distribution", {})
        
        # Get nodes
        nodes = architecture.nodes
        
        if len(nodes) < 2:
            return  # Need at least 2 nodes for connections
            
        # Calculate target connection count based on density
        max_connections = len(nodes) * (len(nodes) - 1)  # Directed graph
        target_connection_count = int(max_connections * connection_density)
        
        # Adjust connection count
        current_count = len(architecture.connections)
        
        if current_count < target_connection_count:
            # Add connections
            for _ in range(current_count, target_connection_count):
                # Choose random source and target nodes
                source_node = random.choice(nodes)
                target_node = random.choice(nodes)
                
                # Skip self-connections
                if source_node.id == target_node.id:
                    continue
                    
                # Check if connection already exists
                exists = any(
                    conn.source_id == source_node.id and conn.target_id == target_node.id
                    for conn in architecture.connections
                )
                
                if not exists:
                    # Determine connection type
                    conn_type = self._select_connection_type(connection_type_dist)
                    
                    # Create connection
                    connection = Connection(
                        id=str(uuid.uuid4()),
                        source_id=source_node.id,
                        target_id=target_node.id,
                        type=conn_type,
                        strength=random.uniform(0.5, 1.0)
                    )
                    
                    architecture.add_connection(connection)
        elif current_count > target_connection_count:
            # Remove connections
            for _ in range(current_count - target_connection_count):
                # Choose a random connection to remove
                if architecture.connections:
                    conn_index = random.randint(0, len(architecture.connections) - 1)
                    conn_id = architecture.connections[conn_index].id
                    architecture.remove_connection(conn_id)
                    
        # Update connection types based on distribution
        for conn in architecture.connections:
            # Randomly decide whether to change this connection's type
            if random.random() < 0.3:  # 30% chance to change
                conn_type = self._select_connection_type(connection_type_dist)
                architecture.update_connection(conn.id, {"type": conn_type})
                
    def _select_connection_type(self, distribution: Dict[str, Any]) -> ConnectionType:
        """
        Select a connection type based on distribution.
        
        Args:
            distribution: Connection type distribution
            
        Returns:
            Selected connection type
        """
        # Get distribution values
        standard = distribution.get("standard", 0.6)
        excitatory = distribution.get("excitatory", 0.2)
        inhibitory = distribution.get("inhibitory", 0.1)
        bidirectional = distribution.get("bidirectional", 0.1)
        
        # Normalize
        total = standard + excitatory + inhibitory + bidirectional
        if total <= 0:
            return ConnectionType.STANDARD
            
        standard /= total
        excitatory /= total
        inhibitory /= total
        bidirectional /= total
        
        # Select type
        r = random.random()
        
        if r < standard:
            return ConnectionType.STANDARD
        elif r < standard + excitatory:
            return ConnectionType.EXCITATORY
        elif r < standard + excitatory + inhibitory:
            return ConnectionType.INHIBITORY
        else:
            return ConnectionType.BIDIRECTIONAL
            
    def _calculate_additional_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Calculate additional derived metrics.
        
        Args:
            metrics: Metrics dictionary to update
        """
        # Calculate efficiency (ratio of connectivity to density)
        if "density" in metrics and metrics["density"] > 0:
            metrics["efficiency"] = metrics["connectivity_ratio"] / metrics["density"]
        else:
            metrics["efficiency"] = 0
            
        # Calculate complexity (derived from network topology)
        if "node_count" in metrics and "connection_count" in metrics:
            node_count = metrics["node_count"]
            connection_count = metrics["connection_count"]
            
            if node_count > 0:
                complexity = connection_count * math.log(node_count) / node_count
                metrics["complexity"] = complexity
            else:
                metrics["complexity"] = 0
                
    @error_boundary
    def _on_clear_results_clicked(self, sender, app_data) -> None:
        """Handle clear results button click."""
        # Show confirmation dialog
        with dpg.window(label="Clear Results", modal=True, width=300, height=100, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Clear all test results?")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._clear_results,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _clear_results(self, sender, app_data, user_data) -> None:
        """Clear all test results."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Clear results
        self.test_results.clear()
        self.selected_result_index = None
        
        # Update UI
        self._update_results_list()
        
        # Reset details
        dpg.set_value(f"{self.tag}_result_details", "Select a result to view details")
        
        # Clear chart
        dpg.set_value(
            self.chart_texture_id, 
            np.zeros((self.chart_height, self.chart_width, 4), dtype=np.float32)
        )
        
    @error_boundary
    def _on_result_selected(self, sender, app_data) -> None:
        """Handle result selection from list."""
        if not app_data and app_data != 0:
            return
            
        # Get selected index
        self.selected_result_index = dpg.get_value(self.results_list_id)
        
        # Update details
        self._update_result_details()
        
    @error_boundary
    def _on_apply_result_clicked(self, sender, app_data) -> None:
        """Handle apply result button click."""
        if self.selected_result_index is None or self.selected_result_index >= len(self.test_results):
            return
            
        # Show confirmation dialog
        with dpg.window(label="Apply Result", modal=True, width=400, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Apply the selected result parameters to the current architecture?")
            dpg.add_text("This will modify the architecture based on the test parameters.")
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes",
                    callback=self._apply_result,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="No",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _apply_result(self, sender, app_data, user_data) -> None:
        """Apply the selected result to the current architecture."""
        # Close dialog
        dpg.delete_item(user_data)
        
        # Get selected result
        result = self.test_results[self.selected_result_index]
        
        # Make a copy of the architecture
        arch_copy = clone_architecture(self.architecture)
        
        # Store parameters
        self.parameters_to_test = result.parameter_values
        
        # Apply node parameters
        self._apply_node_parameters(arch_copy)
        
        # Apply connection parameters
        self._apply_connection_parameters(arch_copy)
        
        # Update architecture
        self.architecture = arch_copy
        
        # Notify of change
        if self.on_architecture_change:
            self.on_architecture_change(self.architecture)
            
        # Show success message
        with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
            result_id = dpg.last_item()
            
            dpg.add_text("Successfully applied parameters to architecture.")
            dpg.add_button(
                label="OK",
                callback=lambda s, a, u: dpg.delete_item(u),
                user_data=result_id,
                width=100
            )
            
    @error_boundary
    def _on_export_clicked(self, sender, app_data) -> None:
        """Handle export results button click."""
        # Show file dialog
        with dpg.window(label="Export Results", modal=True, width=400, height=150, pos=(400, 200)):
            dialog_id = dpg.last_item()
            
            dpg.add_text("Enter the filepath to save results:")
            dpg.add_input_text(
                tag=f"{self.tag}_export_filepath",
                width=-1,
                hint="test_results.json",
                default_value="test_results.json"
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Export",
                    callback=self._export_results,
                    user_data=dialog_id,
                    width=100
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=dialog_id,
                    width=100
                )
                
    def _export_results(self, sender, app_data, user_data) -> None:
        """Export test results to file."""
        # Get filepath
        filepath = dpg.get_value(f"{self.tag}_export_filepath")
        
        # Close dialog
        dpg.delete_item(user_data)
        
        try:
            # Convert results to dict
            results_data = [result.to_dict() for result in self.test_results]
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2)
                
            # Show success message
            with dpg.window(label="Success", modal=True, width=300, height=100, pos=(400, 200)):
                result_id = dpg.last_item()
                
                dpg.add_text(f"Successfully exported to {filepath}")
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
                
                dpg.add_text(f"Error exporting results: {str(e)}")
                dpg.add_button(
                    label="OK",
                    callback=lambda s, a, u: dpg.delete_item(u),
                    user_data=result_id,
                    width=100
                )
                
    def add_test_result(self, result: ParameterTestResult) -> None:
        """
        Add a test result.
        
        Args:
            result: Test result to add
        """
        self.test_results.append(result)
        
        # Update UI
        self._update_results_list()
        
    def import_results(self, filepath: str) -> bool:
        """
        Import test results from file.
        
        Args:
            filepath: Path to results file
            
        Returns:
            True if import was successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                results_data = json.load(f)
                
            # Convert to results
            results = [ParameterTestResult.from_dict(data) for data in results_data]
            
            # Add to results
            self.test_results.extend(results)
            
            # Update UI
            self._update_results_list()
            
            return True
        except Exception as e:
            logger.error(f"Error importing results: {e}")
            return False
            
    def set_architecture(self, architecture: Architecture) -> None:
        """
        Set the architecture to explore.
        
        Args:
            architecture: Architecture to explore
        """
        self.architecture = architecture