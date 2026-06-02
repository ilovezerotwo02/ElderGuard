"""FastAPI Main Application"""
import sys
import os
import shutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from loguru import logger

from app.core.config import settings
from app.api import detection, knowledge
from app.api.schemas import HealthResponse


# Check if running in PyInstaller bundled environment
def get_base_path() -> Path:
    """Get the application base path"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


def get_work_dir() -> Path:
    """Get the working directory (where writable files are stored)"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def extract_static_files(source: Path, dest: Path) -> None:
    """Copy static files from bundled resources to working directory"""
    if not source.exists():
        logger.warning(f"Static file source path does not exist: {source}")
        return

    logger.info(f"Extracting static files: {source} -> {dest}")
    dest.mkdir(exist_ok=True)

    for item in source.iterdir():
        target = dest / item.name
        try:
            if item.is_file():
                if not target.exists():
                    shutil.copy2(item, target)
                    logger.debug(f"Copied: {item.name}")
            elif item.is_dir():
                if not target.exists():
                    shutil.copytree(item, target)
                    logger.debug(f"Copied directory: {item.name}")
        except Exception as e:
            logger.warning(f"Failed to copy file {item.name}: {e}")


# Initialize paths
BASE_PATH = get_base_path()
WORK_DIR = get_work_dir()
STATIC_DIR = WORK_DIR / "static"

# Ensure directories exist
WORK_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Bundled environment: extract static files from exe resources
if getattr(sys, 'frozen', False):
    source_static = BASE_PATH / "static"
    extract_static_files(source_static, STATIC_DIR)

logger.info(f"Base path: {BASE_PATH}")
logger.info(f"Working directory: {WORK_DIR}")
logger.info(f"Static files directory: {STATIC_DIR}")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A multimodal anti-fraud detection system based on large language models, designed specifically for the elderly"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(detection.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        message="ElderGuard anti-fraud protection system is running normally"
    )


# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"Static files mounted: {STATIC_DIR}")


@app.get("/")
async def serve_frontend():
    """Serve the frontend page"""
    frontend_path = STATIC_DIR / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Please create static/index.html file"}


@app.get("/config")
async def serve_config():
    """Serve the configuration page"""
    config_path = STATIC_DIR / "config.html"
    if config_path.exists():
        return FileResponse(config_path)
    return {"message": "Configuration page not found"}


class ConfigRequest(BaseModel):
    mode: str
    ollama_url: str = ""
    model: str = ""
    api_key: str = ""
    base_url: str = ""


@app.post("/api/config")
async def save_config(config: ConfigRequest):
    """Save configuration to .env file"""
    try:
        if config.mode == 'rules':
            env_lines = [
                "USE_RULES_ONLY=True",
                "USE_OLLAMA=False",
                "OPENAI_API_KEY="
            ]
        elif config.mode == 'ollama':
            env_lines = [
                "USE_RULES_ONLY=False",
                "USE_OLLAMA=True",
                f"OLLAMA_BASE_URL={config.ollama_url}",
                f"OLLAMA_MODEL_NAME={config.model}"
            ]
        elif config.mode == 'openai':
            env_lines = [
                "USE_RULES_ONLY=False",
                "USE_OLLAMA=False",
                f"OPENAI_API_KEY={config.api_key}",
                f"OPENAI_API_BASE={config.base_url}",
                f"LLM_MODEL_NAME={config.model}"
            ]
        else:
            return {"status": "error", "message": f"Unknown mode: {config.mode}"}

        env_path = WORK_DIR / ".env"
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(env_lines))

        logger.info(f"Configuration saved: {env_path}")
        return {"status": "success", "message": "Configuration saved"}
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
