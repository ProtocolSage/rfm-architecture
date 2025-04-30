# Node-based Animation Sequencer

## Overview

The Node-based Animation Sequencer is a powerful system for creating dynamic fractal animations in the RFM Architecture. It provides a visual node graph interface that allows users to sequence parameter changes over time, apply easing functions, and chain complex animation behaviors without coding.

The animation sequencer allows users to:

- Create keyframes with different fractal parameters
- Apply various easing functions between keyframes
- Add wait nodes for pauses in the animation
- Add export nodes for saving frames
- Play, pause, and scrub through animations
- Save and load animation sequences
- Combine nodes to create complex motion patterns
- Use mathematical operations to create procedural animations

## Architecture

The Animation Sequencer is built around a node graph model with these key components:

### Animation Graph

The core graph structure:

```python
class AnimationGraph:
    def __init__(self):
        self.nodes = {}
        self.connections = []
        self.start_node = None
        self.end_node = None
    
    def add_node(self, node: AnimationNode) -> str:
        """Add a node to the graph and return its ID."""
        pass
    
    def connect(self, source_id: str, target_id: str, output_name: str = "default", input_name: str = "default"):
        """Connect two nodes in the graph."""
        pass
    
    def remove_node(self, node_id: str):
        """Remove a node and its connections from the graph."""
        pass
    
    def evaluate(self, time: float) -> Dict[str, Any]:
        """Evaluate the graph at a specific time point."""
        pass
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize the graph to a dictionary."""
        pass
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'AnimationGraph':
        """Create a graph from serialized data."""
        pass
```

### Node Types

The animation sequencer supports the following node types:

#### Base Node

```python
class AnimationNode(ABC):
    def __init__(self, id: str = None):
        self.id = id or str(uuid.uuid4())
        self.inputs = {}
        self.outputs = {}
    
    @abstractmethod
    def evaluate(self, time: float, input_values: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the node at a specific time point."""
        pass
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize the node to a dictionary."""
        pass
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'AnimationNode':
        """Create a node from serialized data."""
        pass
```

#### Keyframe Nodes

Keyframe nodes represent specific parameter states at specific times in the animation. They contain:

- Time position (in seconds)
- Complete set of fractal parameters
- Optional label

```python
class KeyframeNode(AnimationNode):
    def __init__(self, keyframes: List[Tuple[float, Any]], easing: str = "linear", id: str = None):
        super().__init__(id)
        self.keyframes = sorted(keyframes, key=lambda k: k[0])
        self.easing = easing
        self.outputs["value"] = None
    
    def evaluate(self, time: float, input_values: Dict[str, Any]) -> Dict[str, Any]:
        # Find surrounding keyframes and interpolate
        # Apply easing function
        # Return interpolated value
        interpolated = self._interpolate(time)
        return {"value": interpolated}
```

#### Parameter Nodes

```python
class ParameterNode(AnimationNode):
    def __init__(self, parameter_name: str, id: str = None):
        super().__init__(id)
        self.parameter_name = parameter_name
        self.outputs["value"] = None
    
    def evaluate(self, time: float, input_values: Dict[str, Any]) -> Dict[str, Any]:
        # Return the current parameter value
        current_value = get_parameter_value(self.parameter_name)
        return {"value": current_value}
```

#### Math Nodes

```python
class MathNode(AnimationNode):
    def __init__(self, operation: str, id: str = None):
        super().__init__(id)
        self.operation = operation  # add, subtract, multiply, divide, etc.
        self.inputs["a"] = 0
        self.inputs["b"] = 0
        self.outputs["result"] = None
    
    def evaluate(self, time: float, input_values: Dict[str, Any]) -> Dict[str, Any]:
        a = input_values.get("a", 0)
        b = input_values.get("b", 0)
        
        # Perform operation
        if self.operation == "add":
            result = a + b
        elif self.operation == "subtract":
            result = a - b
        # etc.
        
        return {"result": result}
```

#### Oscillator Nodes

```python
class OscillatorNode(AnimationNode):
    def __init__(self, type: str = "sine", frequency: float = 1.0, amplitude: float = 1.0, id: str = None):
        super().__init__(id)
        self.type = type  # sine, square, triangle, sawtooth
        self.frequency = frequency
        self.amplitude = amplitude
        self.outputs["value"] = None
    
    def evaluate(self, time: float, input_values: Dict[str, Any]) -> Dict[str, Any]:
        # Calculate oscillation based on time
        if self.type == "sine":
            value = self.amplitude * math.sin(time * self.frequency * 2 * math.pi)
        # etc.
        
        return {"value": value}
```

#### Wait Nodes

Wait nodes create pauses in the animation:

- Time position (in seconds)
- Duration of the pause
- Optional label

#### Export Nodes

Export nodes save frames to disk at specific times:

- Time position (in seconds)
- Output filename
- Image format (PNG, JPG, BMP)
- Optional label

#### Conditional Nodes

```python
class ConditionalNode(AnimationNode):
    def __init__(self, condition: str = "greater_than", id: str = None):
        super().__init__(id)
        self.condition = condition  # greater_than, less_than, equal, etc.
        self.inputs["a"] = 0
        self.inputs["b"] = 0
        self.inputs["if_true"] = 0
        self.inputs["if_false"] = 0
        self.outputs["result"] = None
    
    def evaluate(self, time: float, input_values: Dict[str, Any]) -> Dict[str, Any]:
        a = input_values.get("a", 0)
        b = input_values.get("b", 0)
        
        # Evaluate condition
        if self.condition == "greater_than":
            condition_met = a > b
        # etc.
        
        # Return appropriate value
        result = input_values.get("if_true", 0) if condition_met else input_values.get("if_false", 0)
        return {"result": result}
```

### Animation Engine

The engine that processes and renders animations:

```python
class AnimationEngine:
    def __init__(self, graph: AnimationGraph = None):
        self.graph = graph or AnimationGraph()
        self.current_time = 0.0
        self.duration = 10.0
        self.fps = 30
        self.is_playing = False
    
    def set_graph(self, graph: AnimationGraph):
        """Set the animation graph."""
        pass
    
    def play(self):
        """Start playing the animation."""
        pass
    
    def pause(self):
        """Pause the animation."""
        pass
    
    def stop(self):
        """Stop the animation and reset to beginning."""
        pass
    
    def seek(self, time: float):
        """Seek to a specific time point."""
        pass
    
    def update(self, delta_time: float):
        """Update the animation state."""
        pass
    
    def render_frame(self) -> Dict[str, Any]:
        """Render the current frame of the animation."""
        pass
    
    def export_frames(self, start_time: float, end_time: float, fps: int) -> List[Dict[str, Any]]:
        """Export a range of animation frames."""
        pass
```

## User Interface

The Animation Sequencer includes a custom UI built with DearPyGui:

### Node Editor

```python
class NodeEditor:
    def __init__(self, graph: AnimationGraph = None):
        self.graph = graph or AnimationGraph()
        self.selected_node = None
        self.is_dirty = False
    
    def build(self):
        """Build the node editor UI."""
        pass
    
    def add_node_ui(self, node_type: str):
        """Add a new node to the graph via UI."""
        pass
    
    def delete_selected_node(self):
        """Delete the currently selected node."""
        pass
    
    def create_connection(self, source: str, source_slot: int, target: str, target_slot: int):
        """Create a new connection between nodes."""
        pass
    
    def on_node_selected(self, sender, app_data):
        """Handle node selection event."""
        pass
    
    def on_connection_created(self, sender, app_data):
        """Handle connection creation event."""
        pass
```

### Timeline Control

```python
class TimelineControl:
    def __init__(self, engine: AnimationEngine):
        self.engine = engine
        self.scrubbing = False
    
    def build(self):
        """Build the timeline UI."""
        pass
    
    def play_button_callback(self, sender, app_data):
        """Handle play button click."""
        pass
    
    def pause_button_callback(self, sender, app_data):
        """Handle pause button click."""
        pass
    
    def stop_button_callback(self, sender, app_data):
        """Handle stop button click."""
        pass
    
    def timeline_scrub_callback(self, sender, app_data):
        """Handle timeline scrubbing."""
        pass
    
    def add_keyframe_callback(self, sender, app_data):
        """Add a keyframe at the current time."""
        pass
```

## Usage Examples

### Creating a Simple Animation

```python
# Create a new animation graph
from ui.rfm_ui.components.anim_nodes import AnimationGraph, KeyframeNode, ParameterNode

graph = AnimationGraph()

# Create a parameter node for the 'zoom' parameter
zoom_param = ParameterNode("zoom")
zoom_param_id = graph.add_node(zoom_param)

# Create a keyframe node for zoom animation
zoom_keyframes = [
    (0.0, 1.0),    # Start at zoom level 1.0
    (5.0, 10.0),   # Zoom to 10.0 at 5 seconds
    (10.0, 1.0)    # Back to 1.0 at 10 seconds
]
zoom_keyframe = KeyframeNode(zoom_keyframes, easing="cubic_in_out")
zoom_keyframe_id = graph.add_node(zoom_keyframe)

# Connect the keyframe node to control the parameter
graph.connect(zoom_keyframe_id, zoom_param_id, "value", "value")

# Set up the animation engine
from ui.rfm_ui.components.anim_engine import AnimationEngine

engine = AnimationEngine(graph)
engine.duration = 10.0
engine.fps = 30

# Generate frames
frames = engine.export_frames(0.0, 10.0, 30)
```

### Complex Animation with Math Nodes

```python
# Create a complex animation with oscillation
from ui.rfm_ui.components.anim_nodes import (
    AnimationGraph, OscillatorNode, MathNode, ParameterNode
)

graph = AnimationGraph()

# Create parameter nodes
x_param = ParameterNode("x_position")
y_param = ParameterNode("y_position")
x_param_id = graph.add_node(x_param)
y_param_id = graph.add_node(y_param)

# Create oscillators with different frequencies
x_osc = OscillatorNode("sine", frequency=0.2, amplitude=0.5)
y_osc = OscillatorNode("sine", frequency=0.3, amplitude=0.5)
x_osc_id = graph.add_node(x_osc)
y_osc_id = graph.add_node(y_osc)

# Create math nodes to adjust oscillation range
x_math = MathNode("add")
y_math = MathNode("add")
x_math.inputs["b"] = 0.5  # Center around 0.5
y_math.inputs["b"] = 0.5  # Center around 0.5
x_math_id = graph.add_node(x_math)
y_math_id = graph.add_node(y_math)

# Connect nodes
graph.connect(x_osc_id, x_math_id, "value", "a")
graph.connect(y_osc_id, y_math_id, "value", "a")
graph.connect(x_math_id, x_param_id, "result", "value")
graph.connect(y_math_id, y_param_id, "result", "value")

# Create animation engine
engine = AnimationEngine(graph)
engine.duration = 20.0
```

## Animation Data Format

Animation sequences are stored in JSON format:

```json
{
  "nodes": [
    {
      "id": "node_1",
      "type": "keyframe",
      "params": {
        "keyframes": [
          {"t": 0.0, "value": 1.0},
          {"t": 5.0, "value": 10.0},
          {"t": 10.0, "value": 1.0}
        ],
        "easing": "cubic_in_out"
      }
    },
    {
      "id": "node_2",
      "type": "parameter",
      "params": {
        "name": "zoom"
      }
    }
  ],
  "connections": [
    {
      "from_node": "node_1",
      "to_node": "node_2",
      "from_socket": "value",
      "to_socket": "value"
    }
  ],
  "metadata": {
    "duration": 10.0,
    "name": "Mandelbrot Zoom"
  }
}
```

## Parameter Interpolation

The sequencer intelligently interpolates between different parameter types:

- **Numeric values**: Smooth interpolation based on easing function
- **Colors**: Component-wise interpolation (RGB)
- **Enums/strings**: Discrete transition at the midpoint
- **Boolean values**: Transition at the midpoint

## Integration with Other Systems

The Animation Sequencer integrates with other RFM systems:

1. **Command-Bus**: Animation changes are tracked for undo/redo
2. **Performance Dashboard**: Animation playback performance is monitored
3. **Self-Healing**: Automatic recovery from invalid animation states
4. **Preset Sharing**: Complete animations can be shared via base64 encoding

## Benefits of Node-based Animation

1. **Visual Programming**: Create complex animations without coding
2. **Reusability**: Reuse animation patterns across different projects
3. **Composability**: Combine simple nodes into complex behaviors
4. **Flexibility**: Easily modify animations without breaking the entire sequence
5. **Non-linear Editing**: No need to recreate animations for simple changes

## Future Enhancements

Planned enhancements to the Animation Sequencer include:

1. **Physics Simulation Nodes**: Add physics-based animation capabilities
2. **Audio Reactivity**: Nodes that respond to audio input
3. **Procedural Animation**: Generate animations from algorithms and patterns
4. **Constraint Systems**: Add constraints to maintain specific relationships
5. **Path Animation**: Draw paths for parameters to follow through space