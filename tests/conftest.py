"""Shared pytest fixtures for RFM tests.

These helpers give new tests a deterministic alternative to hard-coded port
8765 and ``time.sleep(2)`` server startup waits.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _pick_free_port() -> int:
    """Bind to port 0 on localhost and return the OS-assigned free port.

    We release the socket immediately; on most kernels the port will still
    be reusable for the next ``listen()`` within a short window. This is
    race-prone in theory but fine for single-box test runs.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_port(host: str, port: int, *, timeout: float = 5.0, poll: float = 0.05) -> None:
    """Block until ``host:port`` accepts a TCP connection, or raise TimeoutError."""
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError as e:
            last_err = e
            time.sleep(poll)
    raise TimeoutError(
        f"Server did not start listening on {host}:{port} within {timeout}s "
        f"(last error: {last_err!r})"
    )


@pytest.fixture
def free_port() -> int:
    """Return an unused TCP port on localhost."""
    return _pick_free_port()


@pytest.fixture
def websocket_server(free_port: int) -> Iterator[Tuple[str, int]]:
    """Spawn ``run_websocket_server.py`` as a subprocess on a free port.

    Yields ``(host, port)`` once the server is actually accepting
    connections (poll every 50ms, fail after 5s). Terminates the subprocess
    in teardown.
    """
    host = "127.0.0.1"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "run_websocket_server.py"),
        "--host", host,
        "--port", str(free_port),
        "--log-level", "info",
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
        text=True,
    )
    try:
        _wait_for_port(host, free_port, timeout=5.0, poll=0.05)
        yield host, free_port
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
