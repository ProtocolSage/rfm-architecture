#!/usr/bin/env python3
import sys
import os

# Add ui directory to path explicitly
project_root = os.path.abspath(os.path.dirname(__file__))
ui_path = os.path.join(project_root, 'ui')
sys.path.insert(0, ui_path)

print("Modified sys.path:")
print(sys.path)

try:
    import rfm_ui
    print('rfm_ui imported successfully')
except ImportError as e:
    print(f'Import error: {e}')