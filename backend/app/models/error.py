"""Error and solution data models."""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LogLine(BaseModel):
    """Parsed log line structure."""
    timestamp: datetime
    device_id: str
    direction: str  # 'in' or 'out'
    content: str
    raw: str = ""


class DetectedError(BaseModel):
    """An error detected in the logs."""
    id: Optional[int] = None
    device_id: str
    timestamp: datetime
    error_line: str
    context: str  # Surrounding lines for AI analysis
    severity: Severity
    pattern_matched: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class Solution(BaseModel):
    """AI-generated solution for an error."""
    id: Optional[int] = None
    error_id: int
    root_cause: str
    impact: str
    solution: str
    prevention: str
    created_at: datetime = Field(default_factory=datetime.now)


class ErrorWithSolution(BaseModel):
    """Combined error and solution for API responses."""
    error: DetectedError
    solution: Optional[Solution] = None


class ErrorListResponse(BaseModel):
    """Paginated list of errors."""
    errors: List[ErrorWithSolution]
    total: int
    page: int
    per_page: int
