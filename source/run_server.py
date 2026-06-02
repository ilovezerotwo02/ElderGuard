"""
Server run module — called by launcher.py (fallback entry point)
Actual startup logic is inlined in launcher.py's _start_server method
"""
import sys
import os
from pathlib import Path

def get_work_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def start():
    """Start the Web server — actual implementation is inlined in launcher.py"""
    from app.main import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, log_level="warning", access_log=False)

if __name__ == "__main__":
    start()
