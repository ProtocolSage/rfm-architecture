#!/usr/bin/env python3
"""
Module Inspector - A diagnostic tool to inspect Python module structures
"""

import os
import sys
import inspect
import importlib
import importlib.util
import logging
import json
import datetime
from types import ModuleType
from typing import Dict, List, Any, Optional, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MODULE_INSPECTOR")

# Output directory for inspection results
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inspection_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Add parent directory to module search path - THIS IS ALL YOU NEED
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Track modules we've already inspected to avoid duplicates
inspected_modules = set()


def import_module_safely(module_path: str) -> Optional[ModuleType]:
    """
    Import a module safely without raising exceptions.
    
    Args:
        module_path: Dot-notated path to the module
        
    Returns:
        Imported module or None if import failed
    """
    try:
        if module_path in sys.modules:
            return sys.modules[module_path]
        
        logger.info(f"Attempting to import: {module_path}")
        
        # Try importing the module
        module = importlib.import_module(module_path)
        return module
    
    except ImportError as e:
        logger.error(f"Failed to import {module_path}: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error importing {module_path}: {e}")
        return None


def get_module_file_info(module: ModuleType) -> Dict[str, Any]:
    """
    Get file information about a module.
    
    Args:
        module: Module to inspect
        
    Returns:
        Dictionary with file information
    """
    info = {
        "file": getattr(module, "__file__", "Unknown"),
        "package": getattr(module, "__package__", ""),
        "name": getattr(module, "__name__", ""),
    }
    
    # Get the file path and check if it exists
    if info["file"] and info["file"] != "Unknown":
        info["exists"] = os.path.exists(info["file"])
        info["size"] = os.path.getsize(info["file"]) if info["exists"] else 0
        info["modified"] = datetime.datetime.fromtimestamp(
            os.path.getmtime(info["file"])
        ).strftime("%Y-%m-%d %H:%M:%S") if info["exists"] else ""
    else:
        info["exists"] = False
        info["size"] = 0
        info["modified"] = ""
    
    return info


def inspect_function(func) -> Dict[str, Any]:
    """
    Inspect a function and return its details.
    
    Args:
        func: Function to inspect
        
    Returns:
        Dictionary with function details
    """
    try:
        # Get function signature
        sig = inspect.signature(func)
        
        # Get parameter details
        parameters = []
        for name, param in sig.parameters.items():
            param_info = {
                "name": name,
                "kind": str(param.kind),
                "has_default": param.default is not param.empty,
            }
            if param.default is not param.empty:
                try:
                    # Try to get a string representation of the default value
                    param_info["default"] = str(param.default)
                except Exception:
                    param_info["default"] = "<<unprintable>>"
            
            parameters.append(param_info)
        
        # Function details
        result = {
            "signature": str(sig),
            "parameters": parameters,
            "docstring": inspect.getdoc(func) or "",
            "module": getattr(func, "__module__", ""),
            "source_file": getattr(inspect.getmodule(func), "__file__", "Unknown"),
        }
        
        # Try to get source code, handle failure gracefully
        try:
            source_lines, _ = inspect.getsourcelines(func)
            result["source"] = "".join(source_lines)
            result["line_number"] = inspect.getsourcelines(func)[1]
        except (IOError, TypeError):
            result["source"] = "<<source not available>>"
            result["line_number"] = -1
        
        return result
    
    except Exception as e:
        logger.error(f"Error inspecting function {func.__name__}: {e}")
        return {
            "error": str(e),
            "name": getattr(func, "__name__", "Unknown"),
            "module": getattr(func, "__module__", "Unknown")
        }


def inspect_class(cls) -> Dict[str, Any]:
    """
    Inspect a class and return its details.
    
    Args:
        cls: Class to inspect
        
    Returns:
        Dictionary with class details
    """
    try:
        # Get methods, filtering out special methods
        methods = {}
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith("__"):
                methods[name] = inspect_function(member)
        
        # Get class attributes
        attributes = {}
        for name, value in inspect.getmembers(cls):
            if not name.startswith("__") and not inspect.isfunction(value) and not inspect.ismethod(value):
                try:
                    attributes[name] = str(value)
                except Exception:
                    attributes[name] = "<<unprintable>>"
        
        # Get base classes
        bases = []
        for base in cls.__bases__:
            if base is not object:
                bases.append({
                    "name": base.__name__,
                    "module": base.__module__
                })
        
        # Class details
        result = {
            "name": cls.__name__,
            "module": cls.__module__,
            "docstring": inspect.getdoc(cls) or "",
            "methods": methods,
            "attributes": attributes,
            "bases": bases
        }
        
        # Try to get source code
        try:
            source_lines, _ = inspect.getsourcelines(cls)
            result["source"] = "".join(source_lines)
            result["line_number"] = inspect.getsourcelines(cls)[1]
        except (IOError, TypeError):
            result["source"] = "<<source not available>>"
            result["line_number"] = -1
        
        return result
    
    except Exception as e:
        logger.error(f"Error inspecting class {cls.__name__}: {e}")
        return {
            "error": str(e),
            "name": cls.__name__,
            "module": cls.__module__
        }


def inspect_module_structure(module_path: str, max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
    """
    Recursively inspect a module and its submodules up to max_depth.
    
    Args:
        module_path: Dot-notated path to the module
        max_depth: Maximum recursion depth for submodules
        current_depth: Current recursion depth
        
    Returns:
        Dictionary with module details
    """
    # Check if we've already inspected this module (to prevent cycles)
    if module_path in inspected_modules:
        return {"name": module_path, "already_inspected": True}
    
    inspected_modules.add(module_path)
    
    # Import the module
    module = import_module_safely(module_path)
    if not module:
        return {"name": module_path, "error": "Import failed"}
    
    # Get module file information
    file_info = get_module_file_info(module)
    
    # Collect all attributes
    attributes = dir(module)
    
    # Filter out built-in attributes
    attributes = [attr for attr in attributes if not attr.startswith("__")]
    
    # Categorize attributes
    functions = {}
    classes = {}
    variables = {}
    submodules = {}
    
    for attr_name in attributes:
        try:
            # Get the attribute
            attr = getattr(module, attr_name)
            
            # Categorize based on type
            if inspect.isfunction(attr):
                functions[attr_name] = inspect_function(attr)
            
            elif inspect.isclass(attr):
                classes[attr_name] = inspect_class(attr)
            
            elif inspect.ismodule(attr):
                # Check if it's a submodule of the current module
                if attr.__name__.startswith(module_path + ".") or attr.__name__ == module_path:
                    if current_depth < max_depth:
                        # Recursively inspect the submodule
                        submodules[attr_name] = inspect_module_structure(
                            attr.__name__, max_depth, current_depth + 1
                        )
                    else:
                        submodules[attr_name] = {"name": attr.__name__, "max_depth_reached": True}
            
            else:
                # It's a variable or other attribute
                try:
                    variables[attr_name] = str(attr)
                except Exception:
                    variables[attr_name] = "<<unprintable>>"
        
        except Exception as e:
            logger.error(f"Error inspecting attribute {attr_name} in {module_path}: {e}")
    
    # Create the result
    result = {
        "name": module_path,
        "file_info": file_info,
        "functions_count": len(functions),
        "classes_count": len(classes),
        "variables_count": len(variables),
        "submodules_count": len(submodules),
        "functions": functions,
        "classes": classes,
        "variables": variables,
        "submodules": submodules
    }
    
    return result


def write_module_report(module_info: Dict[str, Any], file_path: str) -> None:
    """
    Write module inspection results to a file.
    
    Args:
        module_info: Module inspection results
        file_path: Path to write the results to
    """
    try:
        with open(file_path, "w") as f:
            json.dump(module_info, f, indent=2)
        logger.info(f"Module report written to {file_path}")
    except Exception as e:
        logger.error(f"Error writing module report to {file_path}: {e}")


def print_module_summary(module_info: Dict[str, Any], indent: int = 0) -> None:
    """
    Print a summary of the module inspection.
    
    Args:
        module_info: Module inspection results
        indent: Indentation level
    """
    indent_str = "  " * indent
    name = module_info.get("name", "Unknown")
    
    # Handle already inspected modules
    if module_info.get("already_inspected", False):
        print(f"{indent_str}Module {name} (already inspected)")
        return
    
    # Handle import errors
    if "error" in module_info:
        print(f"{indent_str}Module {name} (ERROR: {module_info['error']})")
        return
    
    # Handle max depth reached
    if module_info.get("max_depth_reached", False):
        print(f"{indent_str}Module {name} (max depth reached)")
        return
    
    # Print module summary
    file_path = module_info.get("file_info", {}).get("file", "Unknown")
    functions_count = module_info.get("functions_count", 0)
    classes_count = module_info.get("classes_count", 0)
    variables_count = module_info.get("variables_count", 0)
    submodules_count = module_info.get("submodules_count", 0)
    
    print(f"{indent_str}Module: {name}")
    print(f"{indent_str}  File: {file_path}")
    print(f"{indent_str}  Contents: {functions_count} functions, {classes_count} classes, "
          f"{variables_count} variables, {submodules_count} submodules")
    
    # Print functions
    if functions_count > 0:
        print(f"{indent_str}  Functions:")
        for func_name, func_info in module_info.get("functions", {}).items():
            sig = func_info.get("signature", "")
            print(f"{indent_str}    - {func_name}{sig}")
    
    # Print classes
    if classes_count > 0:
        print(f"{indent_str}  Classes:")
        for class_name, class_info in module_info.get("classes", {}).items():
            method_count = len(class_info.get("methods", {}))
            bases = [base["name"] for base in class_info.get("bases", [])]
            bases_str = f" (inherits: {', '.join(bases)})" if bases else ""
            print(f"{indent_str}    - {class_name}{bases_str} [{method_count} methods]")
            
            # Print top 5 methods for each class
            methods = list(class_info.get("methods", {}).items())
            if methods:
                for i, (method_name, method_info) in enumerate(methods[:5]):
                    sig = method_info.get("signature", "")
                    print(f"{indent_str}      > {method_name}{sig}")
                if len(methods) > 5:
                    print(f"{indent_str}      > ... and {len(methods) - 5} more methods")
    
    # Print submodules (recursive)
    if submodules_count > 0:
        print(f"{indent_str}  Submodules:")
        for submodule_name, submodule_info in module_info.get("submodules", {}).items():
            print_module_summary(submodule_info, indent + 2)


def inspect_all_modules(modules_to_inspect: List[str]) -> None:
    """
    Inspect all specified modules and write reports.
    
    Args:
        modules_to_inspect: List of module paths to inspect
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = {}
    for module_path in modules_to_inspect:
        logger.info(f"Inspecting module: {module_path}")
        
        # Reset the inspected modules set for each top-level module
        inspected_modules.clear()
        
        # Inspect the module
        module_info = inspect_module_structure(module_path, max_depth=2)
        results[module_path] = module_info
        
        # Write a report for this module
        report_file = os.path.join(
            OUTPUT_DIR, 
            f"{timestamp}_{module_path.replace('.', '_')}.json"
        )
        write_module_report(module_info, report_file)
        
        # Print a summary
        print("\n" + "=" * 80)
        print(f"SUMMARY FOR MODULE: {module_path}")
        print("=" * 80)
        print_module_summary(module_info)
        print("=" * 80 + "\n")
    
    # Write a summary report
    summary_file = os.path.join(OUTPUT_DIR, f"{timestamp}_summary.json")
    try:
        with open(summary_file, "w") as f:
            summary = {
                "timestamp": timestamp,
                "modules_inspected": list(modules_to_inspect),
                "python_version": sys.version,
                "platform": sys.platform,
                "module_count": len(results)
            }
            json.dump(summary, f, indent=2)
        logger.info(f"Summary report written to {summary_file}")
    except Exception as e:
        logger.error(f"Error writing summary report: {e}")


if __name__ == "__main__":
    # Define modules to inspect - THESE ARE THE MODULES FROM YOUR PROJECT
    modules_to_inspect = [
        # Core modules
        "rfm.core.fractal",
        "rfm.core.progress",
        "rfm.core.websocket_server",
        
        # UI modules
        "ui.rfm_ui.engine.core",
        "ui.rfm_ui.healing",
        "ui.rfm_ui.websocket_client",
        
        # Database modules
        "rfm.database.connection",
        
        # Visualization modules
        "rfm.viz.components",
        "rfm.viz.effects"
    ]
    
    # Get modules from command line arguments if provided
    if len(sys.argv) > 1:
        modules_to_inspect = sys.argv[1:]
    
    # Run the inspection
    logger.info(f"Starting inspection of {len(modules_to_inspect)} modules")
    inspect_all_modules(modules_to_inspect)
    logger.info("Inspection complete")