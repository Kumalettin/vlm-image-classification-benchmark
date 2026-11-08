"""
Production configuration file for the Multimodal Image Classifier backend.

This configuration should be used in production environments.
Set environment variables for sensitive data.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
PREDICTIONS_DIR = DATA_DIR / "predictions"
RESULTS_DIR = DATA_DIR / "results"
TEMP_DIR = DATA_DIR / "temp"

# Server configuration
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = False

# Security
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production")

# CORS configuration
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

# File upload configuration
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

# Model configuration
DEFAULT_MODEL_CACHE_DIR = MODELS_DIR

# Logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")

# Rate limiting (requests per minute per IP)
RATE_LIMIT_ENABLED = True
RATE_LIMIT_DEFAULT = int(os.environ.get("RATE_LIMIT_DEFAULT", 100))
RATE_LIMIT_MODEL_DOWNLOAD = int(os.environ.get("RATE_LIMIT_MODEL_DOWNLOAD", 5))
RATE_LIMIT_CLASSIFICATION = int(os.environ.get("RATE_LIMIT_CLASSIFICATION", 10))

# Performance settings
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", 300))

# Database (optional, for future use)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Monitoring (optional)
SENTRY_DSN = os.environ.get("SENTRY_DSN")
ENABLE_METRICS = os.environ.get("ENABLE_METRICS", "false").lower() == "true"

def create_directories():
    """Create all necessary directories for the application."""
    directories = [
        DATA_DIR,
        MODELS_DIR,
        PREDICTIONS_DIR,
        RESULTS_DIR,
        TEMP_DIR,
        Path("logs")
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def validate_config():
    """Validate production configuration."""
    errors = []
    
    if not SECRET_KEY:
        errors.append("SECRET_KEY must be set")
    
    if DEBUG:
        errors.append("DEBUG should be False in production")
    
    if HOST == "127.0.0.1":
        errors.append("HOST should be 0.0.0.0 in production")
    
    if errors:
        raise ValueError(f"Production configuration errors: {', '.join(errors)}")
    
    return True
