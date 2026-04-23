# Windows Compatibility Debt

This note records removed Windows-specific workarounds and the current supported
launch paths.

## Supported Launchers

Use the real application entry points instead of patch scripts:

```powershell
.\run_premium_ui.bat
python run_premium_ui.py --config config.yaml --log-dir logs
```

For the system configuration UI:

```powershell
.\run_system_config.bat
python run_system_config.py
```

## Removed Workaround

The old `run_app.ps1` script was intentionally removed.

It was not a clean launcher. It rewrote tracked source files, generated a
`monkey_patch.py` file at runtime, and depended on outdated assumptions such as
`cpu_config.yaml` existing at the repo root. That behavior belongs in source
fixes, not in a startup wrapper.

## Current Rule

If Windows compatibility issues appear, fix them in the codebase and keep the
launchers thin. Do not reintroduce scripts that mutate tracked files before
startup.
