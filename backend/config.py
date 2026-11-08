"""
Configuration file for the Multimodal Image Classifier backend.
Automatically loads environment variables from .env if present.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Load .env file if it exists
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
    except OSError:
        pass

# Data directories
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
PREDICTIONS_DIR = DATA_DIR / "predictions"
RESULTS_DIR = DATA_DIR / "results"
TEMP_DIR = DATA_DIR / "temp"

# Server configuration
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

# Security & CORS configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

# File upload configuration
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

# Model configuration
DEFAULT_MODEL_CACHE_DIR = MODELS_DIR


def create_directories():
    """Create all necessary directories for the application."""
    directories = [
        DATA_DIR,
        MODELS_DIR,
        PREDICTIONS_DIR,
        RESULTS_DIR,
        TEMP_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
