"""Error detection with Huawei VRP-specific patterns and TTL-based deduplication."""
import re
import time
import logging
from typing import List, Optional, Tuple, Dict
from app.config import settings
from app.models.error import LogLine, Severity

logger = logging.getLogger(__name__)

# Deduplication TTL in seconds (5 minutes)
DEDUP_TTL_SECONDS = 300


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
        # TTL-based deduplication: {error_key: timestamp}
        self._seen_errors: Dict[str, float] = {}
    
    def _cleanup_expired(self):
        """Remove expired entries from deduplication cache."""
        current_time = time.time()
        expired_keys = [
            key for key, ts in self._seen_errors.items()
            if current_time - ts > DEDUP_TTL_SECONDS
        ]
        for key in expired_keys:
            del self._seen_errors[key]
        
        if expired_keys:
            logger.debug(f"Cleared {len(expired_keys)} expired dedup entries")
    
    def _is_duplicate(self, error_key: str) -> bool:
        """Check if error is a duplicate within TTL window."""
        self._cleanup_expired()
        
        if error_key in self._seen_errors:
            return True
        
        self._seen_errors[error_key] = time.time()
        return False
    
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
        
        logger.debug(f"Checking {len(lines)} lines for errors")
        
        for line in lines:
            # Check all lines now (removed direction filter for flexibility)
            result = self._check_line(line)
            if result:
                severity, pattern = result
                
                # Deduplication with TTL
                error_key = f"{line.device_id}:{line.content[:100]}"
                if self._is_duplicate(error_key):
                    logger.debug(f"Skipping duplicate error: {error_key[:50]}...")
                    continue
                
                logger.info(f"Detected {severity.value} error: {line.content[:80]}...")
                errors.append((line, severity, pattern))
        
        if lines and not errors:
            logger.debug(f"No errors detected in {len(lines)} lines")
        
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
                    if not self._is_duplicate(error_key):
                        logger.info(f"Detected CRITICAL error in raw text: {line[:80]}...")
                        errors.append((line.strip(), Severity.CRITICAL, pattern.pattern))
                    break
            else:
                for pattern in self._warning_patterns:
                    if pattern.search(line):
                        error_key = f"{device_id}:{line[:100]}"
                        if not self._is_duplicate(error_key):
                            logger.info(f"Detected WARNING in raw text: {line[:80]}...")
                            errors.append((line.strip(), Severity.WARNING, pattern.pattern))
                        break
        
        return errors
    
    def detect_raw(
        self,
        content: str,
        device_id: str = "unknown"
    ) -> List[Tuple[str, Severity, str]]:
        """
        Detect errors in completely raw content (fallback method).
        
        This is used when the parser cannot parse any structured lines.
        
        Args:
            content: Raw log content
            device_id: Device identifier
            
        Returns:
            List of (error_line, severity, matched_pattern) tuples
        """
        logger.debug(f"Using raw detection on {len(content)} chars from {device_id}")
        return self.detect_in_text(content, device_id)
    
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
        logger.info(f"Added new {severity.value} pattern: {pattern}")
    
    def clear_seen(self):
        """Clear the deduplication cache."""
        count = len(self._seen_errors)
        self._seen_errors.clear()
        logger.info(f"Cleared {count} dedup entries")
    
    def get_patterns(self) -> dict:
        """Get current patterns."""
        return {
            "critical": [p.pattern for p in self._critical_patterns],
            "warning": [p.pattern for p in self._warning_patterns]
        }


# Global detector instance
error_detector = ErrorDetector()
