"""
ElderGuard - Main Entry Point (Optimized)
"""

import sys
import os
import webbrowser
import threading
import time
import logging
from pathlib import Path


def setup_logging():
    """Configure logging — show only important info, suppress access logs and SQL log loops"""
    # Clear existing log handlers to avoid duplicates
    for name in list(logging.root.manager.loggerDict.keys()):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = False

    # Set root log level
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)

    # Suppress all unwanted loggers
    loggers = [
        "uvicorn.access",
        "uvicorn.error",
        "uvicorn",
        "fastapi",
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.orm",
        "httptools",
        "websockets",
    ]
    for name in loggers:
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)
        logger.handlers.clear()
        logger.propagate = False


def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)  # Wait for server to start
    url = "http://localhost:8000"
    webbrowser.open(url)


def print_banner():
    """Print startup banner"""
    banner = """\
====================================================
      ElderGuard (Anti-Fraud System)
      AI-Powered Multi-Modal Fraud Detection System
====================================================
    """
    print(banner, flush=True)


def print_startup_info():
    """Print startup info"""
    print("=" * 50)
    print("  System started successfully! Access via:")
    print()
    print("  [1] Detection Page: http://localhost:8000")
    print("  [2] Config Page:    http://localhost:8000/config")
    print("  [3] API Docs:       http://localhost:8000/docs")
    print()
    print("  [!] Browser opened automatically. If not, please visit manually")
    print("  [X] Press Ctrl+C to stop the service")
    print("=" * 50)
    print(flush=True)


def main():
    """Launch the application"""
    # Setup logging
    setup_logging()

    # Print banner
    print_banner()

    # Import app module
    try:
        from app.main import app
    except ImportError as e:
        print(f"\n[ERROR] Failed to import app module: {e}", flush=True)
        input("Press Enter to exit...")
        return

    # Initialize database
    try:
        from app.database.session import engine, Base
        import asyncio
        async def init_db():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            # Initialize sample data (skip if already exists)
            from app.database.init_data import init_sample_data
            await init_sample_data()
        asyncio.run(init_db())
        print("[Database initialized]", flush=True)
    except Exception as e:
        print(f"[WARNING] Database initialization failed: {e}", flush=True)

    # Start browser thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Print startup info
    print_startup_info()

    # Import and start uvicorn with app object instead of string reference
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for packaged builds
        log_level="warning",  # Show warnings and errors only
        access_log=False,  # Disable access logs to avoid loop output
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Service stopped")
    except Exception as e:
        print(f"\n[ERROR] Startup failed: {e}", flush=True)
        input("Press Enter to exit...")
