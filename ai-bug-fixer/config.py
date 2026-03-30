"""
Configuration settings for AI Bug Fixer
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from .env file."""

    # LLM Settings (required)
    LLM_API_KEY: str = os.getenv("LLM_API_KEY")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL")
    LLM_MODEL: str = os.getenv("LLM_MODEL")

    # Embedding Settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # FAISS Settings
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")

    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Streamlit Settings
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        return True


config = Config()
