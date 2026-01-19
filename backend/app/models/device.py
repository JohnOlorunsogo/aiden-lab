"""Device data models."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Device(BaseModel):
    """Monitored device information."""
    id: str  # device_2000, etc.
    name: Optional[str] = None
    log_file: str
    last_seen: datetime = Field(default_factory=datetime.now)
    error_count: int = 0
    status: str = "active"  # active, inactive, error


class DeviceListResponse(BaseModel):
    """List of monitored devices."""
    devices: List[Device]
    total: int
