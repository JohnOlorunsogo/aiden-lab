"""Error detection with Huawei VRP-specific patterns."""
import re
from typing import List, Optional, Tuple
from app.config import settings
from app.models.error import LogLine, Severity


class ErrorDetector:
    """Detects errors in log content using configurable patterns."""
    
    def __init__(self):
        """Initialize detector with patterns from settings."""
        self._critical_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in settings.error_patterns_critical
        ]
        self._warning_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in settings.error_patterns_warning
        ]
        self._seen_errors: set = set()  # For deduplication
    
    def detect_in_lines(
        self, 
        lines: List[LogLine]
    ) -> List[Tuple[LogLine, Severity, str]]:
        """
        Detect errors in a list of parsed log lines.
        
        Args:
            lines: List of LogLine objects
            
        Returns:
            List of (line, severity, matched_pattern) tuples
        """
        errors = []
        
        for line in lines:
            # Only check incoming lines (from device)
            if line.direction != "in":
                continue
            
            result = self._check_line(line)
            if result:
                severity, pattern = result
                
                # Deduplication - skip if we've seen this exact error recently
                error_key = f"{line.device_id}:{line.content[:100]}"
                if error_key in self._seen_errors:
                    continue
                self._seen_errors.add(error_key)
                
                errors.append((line, severity, pattern))
        
        return errors
    
    def detect_in_text(
        self, 
        text: str, 
        device_id: str = "unknown"
    ) -> List[Tuple[str, Severity, str]]:
        """
        Detect errors in raw text content.
        
        Args:
            text: Raw text content
            device_id: Device identifier for deduplication
            
        Returns:
            List of (error_line, severity, matched_pattern) tuples
        """
        errors = []
        
        for line in text.split('\n'):
            if not line.strip():
                continue
            
            # Check against patterns
            for pattern in self._critical_patterns:
                if pattern.search(line):
                    error_key = f"{device_id}:{line[:100]}"
                    if error_key not in self._seen_errors:
                        self._seen_errors.add(error_key)
                        errors.append((line.strip(), Severity.CRITICAL, pattern.pattern))
                    break
            else:
                for pattern in self._warning_patterns:
                    if pattern.search(line):
                        error_key = f"{device_id}:{line[:100]}"
                        if error_key not in self._seen_errors:
                            self._seen_errors.add(error_key)
                            errors.append((line.strip(), Severity.WARNING, pattern.pattern))
                        break
        
        return errors
    
    def _check_line(self, line: LogLine) -> Optional[Tuple[Severity, str]]:
        """
        Check a single line for error patterns.
        
        Returns:
            (Severity, matched_pattern) or None
        """
        content = line.content
        
        # Check critical patterns first
        for pattern in self._critical_patterns:
            if pattern.search(content):
                return (Severity.CRITICAL, pattern.pattern)
        
        # Check warning patterns
        for pattern in self._warning_patterns:
            if pattern.search(content):
                return (Severity.WARNING, pattern.pattern)
        
        return None
    
    def add_pattern(self, pattern: str, severity: Severity):
        """
        Add a new pattern to detect.
        
        Args:
            pattern: Regex pattern string
            severity: Severity level for matches
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        if severity == Severity.CRITICAL:
            self._critical_patterns.append(compiled)
        else:
            self._warning_patterns.append(compiled)
    
    def clear_seen(self):
        """Clear the deduplication cache."""
        self._seen_errors.clear()
    
    def get_patterns(self) -> dict:
        """Get current patterns."""
        return {
            "critical": [p.pattern for p in self._critical_patterns],
            "warning": [p.pattern for p in self._warning_patterns]
        }


# Global detector instance
error_detector = ErrorDetector()
