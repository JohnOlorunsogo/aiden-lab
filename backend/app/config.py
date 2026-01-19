"""Configuration management using Pydantic settings."""
import re
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


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
    
    class Config:
        env_file = ["../.env", ".env"]  # Look in parent dir first, then current
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_db_path(self) -> Path:
        """Extract SQLite database path from URL."""
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return Path("./data/aiden.db")


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.log_watch_dir.mkdir(parents=True, exist_ok=True)
settings.get_db_path().parent.mkdir(parents=True, exist_ok=True)
