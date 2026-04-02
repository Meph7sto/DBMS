"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_default_connection():
    """Return a new dict with default connection parameters."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5438")),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "database": os.getenv("DB_NAME", "postgres"),
    }


API_PREFIX = "/api"
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
