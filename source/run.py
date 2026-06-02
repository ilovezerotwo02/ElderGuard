"""
ElderGuard startup script
"""

import sys
import os
import webbrowser
import threading
import time
import logging
from pathlib import Path


def setup_logging():
    for name in list(logging.root.manager.loggerDict.keys()):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = False

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)

    loggers = [
        "uvicorn.access", "uvicorn.error", "uvicorn",
        "fastapi", "sqlalchemy", "sqlalchemy.engine",
        "sqlalchemy.pool", "sqlalchemy.orm",
        "httptools", "websockets",
    ]
    for name in loggers:
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)
        logger.handlers.clear()
        logger.propagate = False


def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000")


def print_banner():
    print("""
===========================================
  ElderGuard - Anti-Fraud System
===========================================
""", flush=True)


def print_startup_info():
    print("---")
    print("  Server is running!")
    print("  Open http://localhost:8000 in your browser")
    print("  Config page: http://localhost:8000/config")
    print("  Press Ctrl+C to stop")
    print("---", flush=True)


def main():
    setup_logging()
    print_banner()

    try:
        from app.main import app
    except ImportError as e:
        print(f"\n[ERROR] Can't import app: {e}", flush=True)
        input("Press Enter to exit...")
        return

    try:
        from app.database.session import engine, Base
        import asyncio
        async def init_db():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            from app.database.init_data import init_sample_data
            await init_sample_data()
        asyncio.run(init_db())
        print("[DB Ready]", flush=True)
    except Exception as e:
        print(f"[WARN] DB init failed: {e}", flush=True)

    threading.Thread(target=open_browser, daemon=True).start()
    print_startup_info()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, log_level="warning", access_log=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped.")
    except Exception as e:
        print(f"\n[ERROR] {e}", flush=True)
        input("Press Enter to exit...")
