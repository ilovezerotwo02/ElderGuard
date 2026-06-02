"""
Core Configuration Module
"""
import sys
import os
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


def get_env_file_path() -> str:
    """Get the .env file path"""
    if getattr(sys, 'frozen', False):
        # Bundled environment: use the exe directory
        base_dir = Path(sys.executable).parent
    else:
        # Development environment: prefer current working directory
        if (Path.cwd() / ".env").exists():
            return str(Path.cwd() / ".env")
        # Fall back to project root (source/app/core/config.py -> up 4 levels)
        base_dir = Path(__file__).parent.parent.parent.parent

    env_path = base_dir / ".env"
    return str(env_path)


def get_database_url() -> str:
    """Get the database URL"""
    if getattr(sys, 'frozen', False):
        # Bundled environment: database next to exe
        base_dir = Path(sys.executable).parent
        db_path = base_dir / "antifraud.db"
        # Ensure directory exists
        base_dir.mkdir(exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"
    else:
        # Development environment: use relative path
        return "sqlite+aiosqlite:///./antifraud.db"


def get_log_file_path() -> str:
    """Get the log file path"""
    if getattr(sys, 'frozen', False):
        # Bundled environment: logs in logs subdirectory next to exe
        base_dir = Path(sys.executable).parent
        log_dir = base_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        return str(log_dir / "antifraud.log")
    else:
        # Development environment
        return "logs/antifraud.log"


class Settings(BaseSettings):
    """Application Configuration"""

    # Application settings
    APP_NAME: str = "ElderGuard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"

    # Database settings
    DATABASE_URL: str = get_database_url()

    # LLM Configuration
    # Ollama configuration
    USE_OLLAMA: bool = False       # Default: Ollama not enabled
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "deepseek-r1:8b"
    USE_RULES_ONLY: bool = True    # Rules-only mode, no AI models loaded (default on)

    # OpenAI configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL_NAME: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL_NAME: str = "text-embedding-ada-002"

    # Local model configuration
    LOCAL_MODEL_PATH: str = "./models"
    USE_LOCAL_MODEL: bool = False
    LOCAL_MODEL_NAME: str = "facebook/bart-large-mnli"

    # Threat intelligence API
    THREAT_INTEL_API_KEY: Optional[str] = None
    THREAT_INTEL_API_URL: Optional[str] = None

    # Audio detection settings
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_DETECTION_THRESHOLD: float = 0.75

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = get_log_file_path()

    class Config:
        env_file = get_env_file_path()
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# Create global configuration instance
settings = Settings()

# Create necessary directories (using paths consistent with get_log_file_path/get_database_url)
if getattr(sys, 'frozen', False):
    base_dir = Path(sys.executable).parent
else:
    base_dir = Path.cwd()
(base_dir / "logs").mkdir(parents=True, exist_ok=True)
(base_dir / "data").mkdir(parents=True, exist_ok=True)
(base_dir / "models").mkdir(parents=True, exist_ok=True)
