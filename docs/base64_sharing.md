# One-click Preset Sharing

## Overview

The One-click Preset Sharing system in RFM Architecture provides a seamless way for users to share complex fractal configurations and animations with others through compact, portable Base64-encoded URLs. This feature transforms intricate parameter sets into shareable links that can be easily distributed via email, messaging, or social media.

## Architecture

The preset sharing system consists of several key components:

### Encoding Engine

The core component for transforming fractal configurations into shareable formats:

```python
class PresetEncoder:
    def __init__(self, compression_level: int = 9):
        self.compression_level = compression_level
        self.schema_validator = get_schema_validator()
    
    def encode_preset(self, params: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """Encode fractal parameters into a shareable URL."""
        # Validate parameters against schema
        if not self.schema_validator.validate(params):
            raise ValueError("Invalid parameters for encoding")
            
        # Prepare payload with metadata
        payload = {
            "meta": {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "type": "preset",
                **(metadata or {})
            },
            "params": params
        }
        
        # Serialize and compress
        json_data = json.dumps(payload)
        compressed = self._compress(json_data)
        
        # Base64 encode
        encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
        
        # Format as URL
        return f"rfm://preset?data={encoded}"
    
    def _compress(self, json_data: str) -> bytes:
        """Compress JSON data to reduce URL size."""
        return zlib.compress(json_data.encode('utf-8'), self.compression_level)
```

### Decoding Engine

System for securely restoring fractal configurations from shared links:

```python
class PresetDecoder:
    def __init__(self):
        self.schema_validator = get_schema_validator()
        self.security_scanner = get_security_scanner()
    
    def decode_preset(self, share_url: str) -> Dict[str, Any]:
        """Decode a shareable URL into fractal parameters."""
        # Extract base64 data from URL
        match = re.match(r'rfm://preset\?data=(.+)', share_url)
        if not match:
            raise ValueError("Invalid share URL format")
            
        base64_data = match.group(1)
        
        # Decode base64 and decompress
        try:
            compressed = base64.urlsafe_b64decode(base64_data)
            json_data = zlib.decompress(compressed).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decode share URL: {str(e)}")
            
        # Parse JSON
        try:
            payload = json.loads(json_data)
        except json.JSONDecodeError:
            raise ValueError("Corrupted share URL data")
            
        # Security scan
        if not self.security_scanner.scan(payload):
            raise SecurityError("Share URL failed security validation")
            
        # Validate against schema
        if not self.schema_validator.validate(payload.get("params", {})):
            raise ValueError("Invalid parameters in share URL")
            
        return payload.get("params", {})
```

### Security Scanner

Component for validating the safety of shared presets:

```python
class SecurityScanner:
    def __init__(self):
        self.blocklist = self._load_blocklist()
        
    def scan(self, payload: Dict[str, Any]) -> bool:
        """Scan payload for security issues."""
        # Check for suspicious patterns
        serialized = json.dumps(payload)
        
        # Check against blocklist patterns
        for pattern in self.blocklist:
            if re.search(pattern, serialized):
                return False
                
        # Ensure no file paths are included
        if self._contains_file_paths(payload):
            return False
            
        # Additional security checks
        # ...
            
        return True
        
    def _load_blocklist(self) -> List[str]:
        """Load security blocklist patterns."""
        # Load patterns from configuration
        pass
        
    def _contains_file_paths(self, obj: Any) -> bool:
        """Check if object contains file paths."""
        # Recursively check for file path patterns
        pass
```

### Schema Validator

Component for ensuring shared presets adhere to the parameter schema:

```python
class SchemaValidator:
    def __init__(self, schema_path: str = None):
        self.schema = self._load_schema(schema_path)
        
    def validate(self, params: Dict[str, Any]) -> bool:
        """Validate parameters against schema."""
        try:
            jsonschema.validate(params, self.schema)
            return True
        except jsonschema.ValidationError:
            return False
            
    def _load_schema(self, schema_path: str = None) -> Dict[str, Any]:
        """Load parameter schema from file."""
        if schema_path and os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                return json.load(f)
        
        # Use default schema
        return DEFAULT_PARAMETER_SCHEMA
```

## Integration with UI

The One-click Preset Sharing system integrates with the UI to provide:

### Share Button
```python
def create_share_button(ui, params_getter):
    """Create a UI button for generating share links."""
    with ui.panel(label="Share"):
        ui.button(
            label="Create Share Link",
            callback=lambda: on_share_button_click(ui, params_getter())
        )

def on_share_button_click(ui, params):
    """Handle share button click event."""
    encoder = PresetEncoder()
    try:
        share_url = encoder.encode_preset(params)
        pyperclip.copy(share_url)
        ui.toast("Share link copied to clipboard", type="success")
    except Exception as e:
        ui.toast(f"Failed to create share link: {str(e)}", type="error")
```

### Import Dialog
```python
def create_import_dialog(ui, params_setter):
    """Create a dialog for importing presets from share links."""
    with ui.dialog(label="Import Preset"):
        ui.text_input(label="Share Link", id="share_link_input")
        ui.button(
            label="Import",
            callback=lambda: on_import_button_click(
                ui, 
                ui.get_value("share_link_input"),
                params_setter
            )
        )

def on_import_button_click(ui, share_url, params_setter):
    """Handle import button click event."""
    decoder = PresetDecoder()
    try:
        params = decoder.decode_preset(share_url)
        params_setter(params)
        ui.close_dialog()
        ui.toast("Preset imported successfully", type="success")
    except Exception as e:
        ui.toast(f"Failed to import preset: {str(e)}", type="error")
```

## Command-Line Interface

The system includes CLI support for direct loading of presets from share links:

```python
def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="RFM Architecture")
    parser.add_argument(
        "--load",
        dest="share_url",
        help="Load configuration from share URL"
    )
    
    args = parser.parse_args()
    
    if args.share_url:
        decoder = PresetDecoder()
        try:
            params = decoder.decode_preset(args.share_url)
            print(f"Loaded preset with fractal type: {params.get('type')}")
            app = create_app(initial_params=params)
        except Exception as e:
            print(f"Error loading share URL: {str(e)}")
            app = create_app()
    else:
        app = create_app()
        
    app.run()
```

## Usage Examples

### Creating a Share Link

```python
from ui.rfm_ui.sharing.encoder import PresetEncoder

# Create an encoder
encoder = PresetEncoder()

# Prepare fractal parameters
params = {
    "type": "mandelbrot",
    "center_x": -0.743643887037151,
    "center_y": 0.131825904205330,
    "zoom": 4000.0,
    "max_iter": 500,
    "colormap": "viridis",
    "width": 800,
    "height": 600
}

# Generate share link
share_link = encoder.encode_preset(params)
print(share_link)
```

### Importing from a Share Link

```python
from ui.rfm_ui.sharing.decoder import PresetDecoder

# Create a decoder
decoder = PresetDecoder()

# Parse share link
share_link = "rfm://preset?data=eyJtZXRhIjp7InZlcnNpb24iOiIxLjAiLCJjcmVhdGVkIjoiMjAyMy0wNC0zMFQxMjozNToyMyIsInR5cGUiOiJwcmVzZXQifSwicGFyYW1zIjp7InR5cGUiOiJtYW5kZWxicm90IiwiY2VudGVyX3giOi0wLjc0MzY0Mzg4NzAzNzE1MSwiY2VudGVyX3kiOjAuMTMxODI1OTA0MjA1MzMwLCJ6b29tIjo0MDAwLjAsIm1heF9pdGVyIjo1MDAsImNvbG9ybWFwIjoidmlyaWRpcyIsIndpZHRoIjo4MDAsImhlaWdodCI6NjAwfX0="
params = decoder.decode_preset(share_link)

# Use parameters
print(f"Loaded preset with fractal type: {params.get('type')}")
print(f"Center coordinates: ({params.get('center_x')}, {params.get('center_y')})")
print(f"Zoom level: {params.get('zoom')}")
```

### Sharing an Animation

```python
from ui.rfm_ui.sharing.encoder import PresetEncoder
from ui.rfm_ui.components.anim_nodes import AnimationGraph

# Get animation graph
graph = get_current_animation_graph()

# Serialize animation
animation_data = graph.serialize()

# Create encoder
encoder = PresetEncoder()

# Generate share link with animation data
share_link = encoder.encode_preset(
    params={"type": "animation"},
    metadata={"animation": animation_data}
)
print(share_link)
```

## Compression Techniques

The system employs several compression techniques to minimize URL length:

1. **Contextual Compression** - Common parameter sets are recognized and compressed to predefined templates
2. **Delta Encoding** - Only differences from default values are stored
3. **Quantization** - Numeric values are converted to smaller representations where precision isn't critical
4. **Content-aware Compression** - Uses different strategies based on parameter types

## Security Measures

The sharing system implements multiple security features:

1. **Schema Validation** - All parameters are validated against a strict schema
2. **Sanitization** - Input is sanitized to prevent injection attacks
3. **Blocklist Filtering** - Known malicious patterns are blocked
4. **Sandbox Execution** - Imported presets run in a restricted environment
5. **Version Checking** - Ensures compatibility with the current application version

## Benefits of Base64 Sharing

1. **Universal Compatibility** - Works across all platforms and devices
2. **No Server Required** - Completely self-contained sharing mechanism
3. **Privacy** - No tracking or data collection required
4. **Permanence** - Links don't expire or depend on external services
5. **Compactness** - Efficient encoding minimizes URL length

## Future Enhancements

Planned enhancements to the One-click Preset Sharing system include:

1. **Enhanced Compression** - More efficient encoding algorithms
2. **Social Integration** - Direct sharing to social media platforms
3. **QR Code Generation** - Visual representation of share links
4. **Link Shortening** - Optional integration with URL shorteners
5. **Gallery Integration** - Public showcase of shared presets with voting