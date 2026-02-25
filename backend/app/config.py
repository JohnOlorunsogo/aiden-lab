"""Configuration management using Pydantic settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List

try:
    _config_file = os.path.abspath(__file__)
    _config_dir = os.path.dirname(_config_file)
    _backend_dir = os.path.dirname(_config_dir)
    BACKEND_ROOT = Path(_backend_dir)
except Exception:
    BACKEND_ROOT = Path.cwd()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    llm_base_url: str = Field(
        default="http://159.138.135.202:8000",
        description="Base URL of the self-hosted LLM server"
    )
    llm_model: str = Field(
        default="gemma-3-1b-it-GGUF",
        description="Model name for the self-hosted LLM"
    )
    
    log_watch_dir: Path = Field(
        default="data/logs",
        description="Directory containing device log files"
    )
    database_url: str = Field(
        default="sqlite:///./data/aiden.db",
        description="Database connection URL"
    )
    ensp_mode: str = Field(
        default="standard",
        description="ENSP logger mode: standard, extended, lab, or custom"
    )
    ensp_console_port_range: str = Field(
        default="2000-2004",
        description="Console port range for eNSP (e.g., '2000-2004' or '2000,2001,2002')"
    )
    ensp_auto_detect: bool = Field(
        default=True,
        description="Auto-detect active console ports"
    )
    ensp_loopback_iface: str = Field(
        default="Npcap Loopback Adapter",
        description="Network interface name for loopback packet capture"
    )
    ensp_sniffer_log_dir: str = Field(
        default="",
        description="Custom log directory for ENSP sniffer (empty = use log_watch_dir for unified build)"
    )
    ensp_logger_enabled: bool = Field(
        default=True,
        description="Enable/disable ENSP packet sniffer"
    )
    ensp_capture_mode: str = Field(
        default="proxy",
        description="Capture mode: 'proxy' (Telnet proxy, recommended) or 'sniffer' (passive packet capture)"
    )
    ensp_proxy_port_offset: int = Field(
        default=1000,
        description="Port offset for Telnet proxy (e.g., 1000 means eNSP port 2000 → proxy port 3000)"
    )
    ensp_target_host: str = Field(
        default="127.0.0.1",
        description="Host where eNSP is running (for proxy to connect to)"
    )
    
    context_lines: int = Field(
        default=30,
        description="Number of context lines to extract around errors"
    )
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
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    @field_validator('log_watch_dir', mode='before')
    @classmethod
    def resolve_log_path(cls, v):
        if v is None:
            v = "data/logs"
        
        if isinstance(v, Path):
            path = v
        else:
            path_str = str(v).strip()
            if path_str.startswith('./'):
                path_str = path_str[2:]
            path = Path(path_str)
        
        if path.is_absolute():
            return path
        
        if BACKEND_ROOT.is_absolute():
            return BACKEND_ROOT / path
        else:
            return Path.cwd() / BACKEND_ROOT / path
    
    class Config:
        env_file = ["../.env", ".env"]
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_db_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            path = Path(db_path)
            if not path.is_absolute():
                path_str = str(path)
                if path_str.startswith('./'):
                    path_str = path_str[2:]
                return BACKEND_ROOT / path_str
            return path
        return BACKEND_ROOT / "data" / "aiden.db"


settings = Settings()

settings.log_watch_dir.mkdir(parents=True, exist_ok=True)
settings.get_db_path().parent.mkdir(parents=True, exist_ok=True)

MODE_CONFIGS = {
    "standard": {
        "port_range": "2000-2004",
        "auto_detect": True,
    },
    "extended": {
        "port_range": "2000-2010",
        "auto_detect": True,
    },
    "lab": {
        "port_range": "2000-2020",
        "auto_detect": True,
    },
    "custom": {
        "port_range": "2000-2004",
        "auto_detect": False,
    }
}

if settings.ensp_mode in MODE_CONFIGS:
    mode_config = MODE_CONFIGS[settings.ensp_mode]
    if settings.ensp_console_port_range == "2000-2004" and settings.ensp_mode != "standard":
        settings.ensp_console_port_range = mode_config["port_range"]
    if settings.ensp_auto_detect == True and settings.ensp_mode == "custom":
        settings.ensp_auto_detect = mode_config["auto_detect"]
