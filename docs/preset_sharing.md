# Preset Sharing in RFM Architecture

The RFM Architecture visualization system includes a powerful preset sharing capability that allows users to save, export, and share their fractal configurations.

## Overview

Preset sharing enables:

- Saving and loading fractal configurations
- Exporting configurations as compact share links
- Loading presets directly from share links via command line
- Cross-platform compatibility for shared presets

## Share Link Format

Share links use the following format:

```
rfm://preset?data=BASE64ENCODED_JSON
```

Where `BASE64ENCODED_JSON` is a base64-encoded JSON object containing:

```json
{
  "meta": {
    "version": "1.0",
    "created": "ISO_TIMESTAMP",
    "type": "preset"
  },
  "params": {
    // Fractal parameters...
  }
}
```

## Creating Share Links

### From UI

1. Create a fractal configuration you want to share
2. Click **Save Preset** in the presets panel
3. Enter a name for your preset
4. Ensure "Create shareable link" is checked
5. Click **Save**
6. Click **Copy to Clipboard** to copy the share link

### Programmatically

```python
from rfm_ui.utils.share import encode_preset

params = {
    "type": "mandelbrot",
    "center_x": -0.743643887037151,
    "center_y": 0.131825904205330,
    "zoom": 4000.0,
    "max_iter": 500,
    "colormap": "viridis"
}

share_link = encode_preset(params)
print(share_link)
```

## Using Share Links

### From Command Line

To load a preset directly from a share link:

```bash
python run_premium_ui.py --load "rfm://preset?data=..."
```

### Programmatically

```python
from rfm_ui.utils.share import decode_preset, validate_preset

# Decode the share link
params = decode_preset(share_link)

# Validate the parameters
if validate_preset(params):
    # Use the parameters
    print(f"Loaded valid preset with fractal type: {params.get('type')}")
else:
    print("Invalid preset parameters")
```

## Example Share Links

Below are some example share links for interesting fractal configurations:

### Mandelbrot - Deep Zoom

```
rfm://preset?data=eyJtZXRhIjp7InZlcnNpb24iOiIxLjAiLCJjcmVhdGVkIjoiMjAyMy0wNC0zMFQxMjozNToyMyIsInR5cGUiOiJwcmVzZXQifSwicGFyYW1zIjp7InR5cGUiOiJtYW5kZWxicm90IiwiY2VudGVyX3giOi0wLjc0MzY0Mzg4NzAzNzE1MSwiY2VudGVyX3kiOjAuMTMxODI1OTA0MjA1MzMwLCJ6b29tIjo0MDAwLjAsIm1heF9pdGVyIjo1MDAsImNvbG9ybWFwIjoidmlyaWRpcyIsIndpZHRoIjo4MDAsImhlaWdodCI6NjAwfX0=
```

### Julia Set - Dendrite

```
rfm://preset?data=eyJtZXRhIjp7InZlcnNpb24iOiIxLjAiLCJjcmVhdGVkIjoiMjAyMy0wNC0zMFQxMjozNjoxNSIsInR5cGUiOiJwcmVzZXQifSwicGFyYW1zIjp7InR5cGUiOiJqdWxpYSIsImNfcmVhbCI6MC4wLCJjX2ltYWciOjEuMCwiY2VudGVyX3giOjAuMCwiY2VudGVyX3kiOjAuMCwiem9vbSI6MS41LCJtYXhfaXRlciI6MTAwLCJjb2xvcm1hcCI6Im1hZ21hIiwid2lkdGgiOjgwMCwiaGVpZ2h0Ijo2MDB9fQ==
```

## Security Considerations

Share links contain only fractal parameters and never include:

- Personal information
- File paths
- System configuration
- Sensitive data

All data is validated before use to prevent injection attacks.

## Implementation Details

The preset sharing system consists of:

1. **Encoder** - Converts parameters to shareable links
2. **Decoder** - Processes and validates share links
3. **Validation** - Ensures parameters are safe and valid
4. **UI Integration** - User-friendly interface for creating and using share links
5. **CLI Support** - Command-line parameter for direct loading of share links