# Running RFM Architecture on Windows (WSL2)

This document provides instructions for running the RFM Architecture application on Windows using WSL2.

## Known Issues and Fixes

The RFM Architecture codebase was designed primarily for Unix-like systems and has a few compatibility issues when running on Windows:

1. **Signal Handling**: Windows does not support Unix signals like SIGUSR1 and SIGUSR2, which are used in the WebSocket server.
2. **Import Issues**: There are relative import problems in the system_config modules that need to be fixed.
3. **Missing Methods**: The `structured_log` method is missing from the standard Logger class.
4. **Self-Healing Decorator**: The `self_healing` decorator is referenced but not implemented.

## Quick Start

To run the application with all fixes applied, use the provided PowerShell script:

```powershell
# From the project root directory
.\run_app.ps1
```

By default, this will run the Premium UI with the `cpu_config.yaml` configuration. You can specify a different configuration:

```powershell
.\run_app.ps1 -ConfigFile "custom_config.yaml" -LogDir "custom_logs"
```

## What the Fix Script Does

The `run_app.ps1` script performs several fixes before running the application:

1. Clears Python bytecode cache to avoid stale imports
2. Fixes relative imports in system_config modules:
   - Changes `from ..errors.decorators import error_boundary` to `from rfm_ui.errors import error_boundary`
   - Changes `from ..healing.decorators import self_healing` to `from rfm_ui.healing.decorators import self_healing`
3. Adds the missing `self_healing` decorator to the healing module if needed
4. Creates a monkey patch for the `structured_log` method and Windows signal handling
5. Sets the PYTHONPATH environment variable for proper module resolution
6. Runs the Premium UI with the specified configuration

## Manual Fixes

If you prefer to apply the fixes manually:

### 1. Fix Module Imports

Edit the following files to use absolute imports:

- `ui/rfm_ui/components/system_config/manager.py`
- `ui/rfm_ui/components/system_config/editor.py`
- `ui/rfm_ui/components/system_config/comparison.py`

### 2. Add Self-Healing Decorator

Add the following code to `ui/rfm_ui/healing/decorators.py`:

```python
def self_healing(strategy: str = None, error_types: Optional[List[Type[Exception]]] = None):
    """
    Decorator to add self-healing to a function.
    
    This is an alias for with_healing that also accepts a strategy name.
    
    Args:
        strategy: Strategy name to use for healing
        error_types: Types of errors to handle, or None for all
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Just use with_healing for now
            healer = with_healing(error_types)
            decorated_func = healer(func)
            return decorated_func(*args, **kwargs)
        
        return wrapper
    
    return decorator
```

### 3. Set PYTHONPATH

```powershell
$env:PYTHONPATH = "$PWD"
```

### 4. Run with the Monkey Patch

```powershell
python -c "import monkey_patch; exec(open('run_premium_ui.py').read())" -B --config cpu_config.yaml --log-dir logs
```

## Troubleshooting

If you encounter issues:

1. **Clear Python Cache**: Delete all `__pycache__` directories and `.pyc` files
2. **Check Imports**: Verify that all imports use absolute paths (rfm_ui.*)
3. **Check PYTHONPATH**: Ensure the project root is in your PYTHONPATH
4. **Check Log Files**: Review logs in the specified log directory for errors