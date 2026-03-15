#!/usr/bin/env python3
"""Local development startup script for NyxAI.

This script provides a convenient way to start the NyxAI application
in local development mode with embedded databases.

Usage:
    python scripts/dev-start.py
    python scripts/dev-start.py --reload  # Auto-reload on code changes
    python scripts/dev-start.py --port 8080  # Use custom port
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def setup_environment():
    """Setup environment variables for local development."""
    # Ensure data directory exists
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set default environment variables for embedded mode
    env_vars = {
        "NYX_ENV": "development",
        "NYX_DEBUG": "true",
        "NYX_DB_URL": "sqlite+aiosqlite:///./data/nyxai.db",
        "NYX_DB_ECHO": "false",
        "NYX_VECTOR_ENABLED": "true",
        "NYX_VECTOR_PERSIST_DIRECTORY": "./data/vector_db",
        "NYX_VECTOR_COLLECTION_NAME": "incidents",
        "NYX_LOG_LEVEL": "INFO",
        "NYX_LOG_FORMAT": "console",
        "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"  Set {key}={value}")


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import sqlalchemy
        import chromadb
        print("  Dependencies check passed")
        return True
    except ImportError as e:
        print(f"  Error: Missing dependency - {e}")
        print("  Please install dependencies: pip install -e .")
        return False


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the development server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload on code changes
    """
    cmd = [
        sys.executable, "-m", "uvicorn",
        "nyxai.api.main:app",
        "--host", host,
        "--port", str(port),
    ]
    
    if reload:
        cmd.append("--reload")
        cmd.extend(["--reload-dir", "src/nyxai"])
    
    print(f"\n  Starting server on http://{host}:{port}")
    print(f"  API docs: http://{host}:{port}/docs")
    print(f"  Health check: http://{host}:{port}/health")
    print(f"  Press Ctrl+C to stop\n")
    
    try:
        subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    except KeyboardInterrupt:
        print("\n  Server stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start NyxAI in local development mode"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("NyxAI Local Development Startup")
    print("=" * 60)
    
    print("\n1. Setting up environment...")
    setup_environment()
    
    print("\n2. Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("\n3. Starting server...")
    start_server(args.host, args.port, args.reload)


if __name__ == "__main__":
    main()
