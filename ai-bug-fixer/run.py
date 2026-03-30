#!/usr/bin/env python3
"""
Script to start both backend and frontend services
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path


def get_python_executable():
    """Get the path to the python executable in the venv if it exists."""
    base_path = Path(__file__).parent
    venv_python = base_path / "venv" / "bin" / "python"
    
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def run_backend(python_exe):
    """Start the FastAPI backend server."""
    print(f"Starting backend server using {python_exe}...")
    return subprocess.Popen(
        [
            python_exe,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


def run_frontend(python_exe):
    """Start the Streamlit frontend server."""
    print(f"Starting frontend server using {python_exe}...")
    return subprocess.Popen(
        [
            python_exe,
            "-m",
            "streamlit",
            "run",
            "frontend/app.py",
            "--server.port",
            "8501",
        ],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


def main():
    """Main entry point."""
    print("=" * 50)
    print("AI Bug Fixer")
    print("=" * 50)

    python_exe = get_python_executable()
    backend_proc = None
    frontend_proc = None

    try:
        # Start backend
        backend_proc = run_backend(python_exe)
        time.sleep(3)  # Give backend time to start

        # Start frontend
        frontend_proc = run_frontend(python_exe)

        print("\n" + "=" * 50)
        print("Services started!")
        print("Backend API: http://localhost:8000")
        print("Frontend UI: http://localhost:8501")
        print("=" * 50)
        print("\nPress Ctrl+C to stop all services (logs will appear above)...")

        # Keep running and check if processes are alive
        while True:
            if backend_proc.poll() is not None:
                print("\nERROR: Backend process terminated unexpectedly!")
                break
            if frontend_proc.poll() is not None:
                print("\nERROR: Frontend process terminated unexpectedly!")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutting down services...")
    finally:
        # Cleanup
        if backend_proc:
            backend_proc.terminate()
            backend_proc.wait()
        if frontend_proc:
            frontend_proc.terminate()
            frontend_proc.wait()
        print("All services stopped.")


if __name__ == "__main__":
    main()
