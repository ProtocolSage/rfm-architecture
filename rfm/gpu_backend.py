"""Numba-CUDA fallback to CPU for Mandelbrot / Julia rendering."""
from __future__ import annotations

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, Union

try:
    from numba import cuda, njit, prange
    CUDA_AVAILABLE = cuda.is_available()
except ImportError:
    # Create dummy functions if numba is not available
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator

    def prange(*args, **kwargs):
        return range(*args, **kwargs)
    
    # Create dummy cuda module
    class DummyCuda:
        def __getattr__(self, name):
            return self
        
        def __call__(self, *args, **kwargs):
            return self
        
        def is_available(self):
            return False
            
    cuda = DummyCuda()
    CUDA_AVAILABLE = False

# Set up logger
logger = logging.getLogger("gpu_backend")

# --- CUDA kernel for Mandelbrot set ---
@cuda.jit
def _mandelbrot_cuda(min_x, max_x, min_y, max_y, image, max_iter):
    """CUDA kernel for Mandelbrot set calculation."""
    height = image.shape[0]
    width = image.shape[1]
    pixel_x, pixel_y = cuda.grid(2)

    if pixel_x < width and pixel_y < height:
        # Map pixel coordinates to complex plane
        dx = max_x - min_x
        dy = max_y - min_y
        x0 = min_x + pixel_x * dx / width
        y0 = min_y + pixel_y * dy / height
        
        # Mandelbrot iteration
        x, y = 0.0, 0.0
        iteration = 0
        
        while (x*x + y*y <= 4.0) and iteration < max_iter:
            x, y = x*x - y*y + x0, 2*x*y + y0
            iteration += 1
            
        # Store iteration count
        image[pixel_y, pixel_x] = iteration

# --- CUDA kernel for Julia set ---
@cuda.jit
def _julia_cuda(min_x, max_x, min_y, max_y, image, max_iter, c_real, c_imag):
    """CUDA kernel for Julia set calculation."""
    height = image.shape[0]
    width = image.shape[1]
    pixel_x, pixel_y = cuda.grid(2)

    if pixel_x < width and pixel_y < height:
        # Map pixel coordinates to complex plane
        dx = max_x - min_x
        dy = max_y - min_y
        x = min_x + pixel_x * dx / width
        y = min_y + pixel_y * dy / height
        
        # Julia iteration
        iteration = 0
        
        while (x*x + y*y <= 4.0) and iteration < max_iter:
            x, y = x*x - y*y + c_real, 2*x*y + c_imag
            iteration += 1
            
        # Store iteration count
        image[pixel_y, pixel_x] = iteration

# --- CPU fallback for Mandelbrot set (Numba-jit) ---
@njit(parallel=True, fastmath=True)
def _mandelbrot_cpu(min_x, max_x, min_y, max_y, max_iter, res):
    """CPU implementation of Mandelbrot set calculation."""
    height, width = res
    image = np.zeros((height, width), dtype=np.uint16)
    
    for y in prange(height):
        for x in prange(width):
            # Map pixel coordinates to complex plane
            cx = min_x + (max_x - min_x) * x / width
            cy = min_y + (max_y - min_y) * y / height
            
            # Mandelbrot iteration
            zx, zy = 0.0, 0.0
            iteration = 0
            
            while zx*zx + zy*zy <= 4.0 and iteration < max_iter:
                zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
                iteration += 1
                
            image[y, x] = iteration
            
    return image

# --- CPU fallback for Julia set (Numba-jit) ---
@njit(parallel=True, fastmath=True)
def _julia_cpu(min_x, max_x, min_y, max_y, max_iter, c_real, c_imag, res):
    """CPU implementation of Julia set calculation."""
    height, width = res
    image = np.zeros((height, width), dtype=np.uint16)
    
    for y in prange(height):
        for x in prange(width):
            # Map pixel coordinates to complex plane
            zx = min_x + (max_x - min_x) * x / width
            zy = min_y + (max_y - min_y) * y / height
            
            # Julia iteration
            iteration = 0
            
            while zx*zx + zy*zy <= 4.0 and iteration < max_iter:
                zx, zy = zx*zx - zy*zy + c_real, 2*zx*zy + c_imag
                iteration += 1
                
            image[y, x] = iteration
            
    return image

# --- Public API ---

def mandelbrot(params: Dict[str, Any]) -> np.ndarray:
    """
    Compute Mandelbrot set with auto GPU selection.
    
    Args:
        params: Dictionary with parameters
            - center_x: x-coordinate of center point
            - center_y: y-coordinate of center point
            - zoom: zoom level
            - max_iter: maximum iterations
            - width: image width
            - height: image height
            
    Returns:
        Array of iteration counts with shape (height, width)
    """
    # Extract parameters with defaults
    width = params.get("width", 800)
    height = params.get("height", 600)
    center_x = params.get("center_x", -0.5)
    center_y = params.get("center_y", 0.0)
    zoom = params.get("zoom", 1.0)
    max_iter = params.get("max_iter", 100)
    
    # Calculate aspect ratio
    aspect_ratio = width / height
    
    # Calculate bounds
    x_range = 4.0 / zoom
    y_range = x_range / aspect_ratio
    
    min_x = center_x - x_range / 2
    max_x = center_x + x_range / 2
    min_y = center_y - y_range / 2
    max_y = center_y + y_range / 2
    
    # Track if GPU was used
    used_gpu = False
    
    # Try GPU if available
    if CUDA_AVAILABLE:
        try:
            # Allocate output array on device
            d_image = cuda.device_array((height, width), dtype=np.uint16)
            
            # Configure CUDA grid
            threadsperblock = (16, 16)
            blockspergrid_x = (width + threadsperblock[0] - 1) // threadsperblock[0]
            blockspergrid_y = (height + threadsperblock[1] - 1) // threadsperblock[1]
            blockspergrid = (blockspergrid_x, blockspergrid_y)
            
            # Launch kernel
            _mandelbrot_cuda[blockspergrid, threadsperblock](
                min_x, max_x, min_y, max_y, d_image, max_iter
            )
            
            # Copy result back to host
            image = d_image.copy_to_host()
            used_gpu = True
            
        except Exception as e:
            logger.warning(f"CUDA Mandelbrot computation failed, falling back to CPU: {str(e)}")
            # Fall back to CPU
            image = _mandelbrot_cpu(min_x, max_x, min_y, max_y, max_iter, (height, width))
    else:
        # Use CPU
        image = _mandelbrot_cpu(min_x, max_x, min_y, max_y, max_iter, (height, width))
    
    logger.info(f"Computed Mandelbrot set using {'GPU' if used_gpu else 'CPU'}")
    return image

def julia(params: Dict[str, Any]) -> np.ndarray:
    """
    Compute Julia set with auto GPU selection.
    
    Args:
        params: Dictionary with parameters
            - c_real: real part of c parameter
            - c_imag: imaginary part of c parameter
            - center_x: x-coordinate of center point
            - center_y: y-coordinate of center point
            - zoom: zoom level
            - max_iter: maximum iterations
            - width: image width
            - height: image height
            
    Returns:
        Array of iteration counts with shape (height, width)
    """
    # Extract parameters with defaults
    width = params.get("width", 800)
    height = params.get("height", 600)
    c_real = params.get("c_real", -0.7)
    c_imag = params.get("c_imag", 0.27)
    center_x = params.get("center_x", 0.0)
    center_y = params.get("center_y", 0.0)
    zoom = params.get("zoom", 1.5)
    max_iter = params.get("max_iter", 100)
    
    # Calculate aspect ratio
    aspect_ratio = width / height
    
    # Calculate bounds
    x_range = 4.0 / zoom
    y_range = x_range / aspect_ratio
    
    min_x = center_x - x_range / 2
    max_x = center_x + x_range / 2
    min_y = center_y - y_range / 2
    max_y = center_y + y_range / 2
    
    # Track if GPU was used
    used_gpu = False
    
    # Try GPU if available
    if CUDA_AVAILABLE:
        try:
            # Allocate output array on device
            d_image = cuda.device_array((height, width), dtype=np.uint16)
            
            # Configure CUDA grid
            threadsperblock = (16, 16)
            blockspergrid_x = (width + threadsperblock[0] - 1) // threadsperblock[0]
            blockspergrid_y = (height + threadsperblock[1] - 1) // threadsperblock[1]
            blockspergrid = (blockspergrid_x, blockspergrid_y)
            
            # Launch kernel
            _julia_cuda[blockspergrid, threadsperblock](
                min_x, max_x, min_y, max_y, d_image, max_iter, c_real, c_imag
            )
            
            # Copy result back to host
            image = d_image.copy_to_host()
            used_gpu = True
            
        except Exception as e:
            logger.warning(f"CUDA Julia computation failed, falling back to CPU: {str(e)}")
            # Fall back to CPU
            image = _julia_cpu(min_x, max_x, min_y, max_y, max_iter, c_real, c_imag, (height, width))
    else:
        # Use CPU
        image = _julia_cpu(min_x, max_x, min_y, max_y, max_iter, c_real, c_imag, (height, width))
    
    logger.info(f"Computed Julia set using {'GPU' if used_gpu else 'CPU'}")
    return image