"""Configuration management using Pydantic settings."""
import re
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List


# Determine project root (parent of backend directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/app/config.py -> project root


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    
    # Paths
    log_watch_dir: Path = Field(
        default=Path("./data/logs"),
        description="Directory containing device log files"
    )
    database_url: str = Field(
        default="sqlite:///./data/aiden.db",
        description="Database connection URL"
    )
    
    # Processing
    context_lines: int = Field(
        default=30,
        description="Number of context lines to extract around errors"
    )
    
    # Error patterns (Huawei VRP specific)
    error_patterns_critical: List[str] = Field(
        default=[
            r"Error:\s*",
            r"failed",
            r"failure",
            r"Unrecognized command",
            r"Permission denied",
            r"Interface\s+\S+\s+is\s+down",
            r"OSPF.*neighbor.*down",
            r"BGP.*connection.*failed",
            r"link\s+down",
        ],
        description="Regex patterns for critical errors"
    )
    
    error_patterns_warning: List[str] = Field(
        default=[
            r"Warning:",
            r"timeout",
            r"console time out",
            r"retrying",
            r"unstable",
        ],
        description="Regex patterns for warnings"
    )
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Log file format regex
    log_line_pattern: str = Field(
        default=r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+\[(\w+)\]\s+([←→])\s+'(.+)'",
        description="Regex pattern to parse log lines"
    )
    
    @field_validator('log_watch_dir', mode='before')
    @classmethod
    def resolve_log_path(cls, v):
        """Resolve log_watch_dir path - handles both relative and absolute paths."""
        if v is None:
            v = "./data/logs"
        
        path = Path(v)
        
        # If it's an absolute path, use it directly
        if path.is_absolute():
            return path
        
        # For relative paths, resolve from:
        # 1. First check if it exists relative to CWD
        if (Path.cwd() / path).exists():
            return Path.cwd() / path
        
        # 2. Otherwise resolve from project root
        return PROJECT_ROOT / path
    
    class Config:
        env_file = ["../.env", ".env"]  # Look in parent dir first, then current
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_db_path(self) -> Path:
        """Extract SQLite database path from URL."""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            path = Path(db_path)
            if not path.is_absolute():
                return Path.cwd() / path
            return path
        return Path("./data/aiden.db")


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.log_watch_dir.mkdir(parents=True, exist_ok=True)
settings.get_db_path().parent.mkdir(parents=True, exist_ok=True)

