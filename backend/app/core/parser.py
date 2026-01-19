"""Log line parser for Huawei ENSP telnet session logs."""
import re
from datetime import datetime
from typing import Optional, List
from app.models.error import LogLine


class LogParser:
    """Parser for Huawei ENSP telnet log format."""
    
    # Pattern: [2026-01-18 03:10:25] [device_2000] ← 'content\r'
    LOG_LINE_PATTERN = re.compile(
        r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+\[(\w+)\]\s+([←→])\s+'(.*)'"
    )
    
    # ANSI escape sequences and control characters
    ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    CONTROL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
    
    @classmethod
    def parse_line(cls, raw: str) -> Optional[LogLine]:
        """
        Parse a single log line.
        
        Args:
            raw: Raw log line string
            
        Returns:
            LogLine object or None if line doesn't match format
        """
        match = cls.LOG_LINE_PATTERN.match(raw.strip())
        if not match:
            return None
        
        timestamp_str, device_id, direction, content = match.groups()
        
        return LogLine(
            timestamp=datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"),
            device_id=device_id,
            direction="in" if direction == "←" else "out",
            content=cls.clean_content(content),
            raw=raw
        )
    
    @classmethod
    def clean_content(cls, content: str) -> str:
        """
        Clean log content by removing escape sequences and control characters.
        
        Args:
            content: Raw content string
            
        Returns:
            Cleaned content string
        """
        # Remove ANSI escape sequences
        cleaned = cls.ESCAPE_PATTERN.sub('', content)
        
        # Remove control characters (but keep newlines for multi-line content)
        cleaned = cls.CONTROL_CHARS.sub('', cleaned)
        
        # Remove trailing \r
        cleaned = cleaned.rstrip('\r')
        
        # Handle doubled characters from terminal echo (common in telnet)
        # This is a simplistic approach - may need refinement
        cleaned = cls._remove_echo_doubles(cleaned)
        
        return cleaned.strip()
    
    @classmethod
    def _remove_echo_doubles(cls, text: str) -> str:
        """
        Remove doubled characters that result from terminal echo.
        Example: 'ddiissppllaayy' -> 'display'
        """
        if len(text) < 2:
            return text
        
        # Check if text appears to be doubled
        result = []
        i = 0
        while i < len(text):
            if i + 1 < len(text) and text[i] == text[i + 1]:
                result.append(text[i])
                i += 2
            else:
                # Not doubled - return original
                return text
        
        return ''.join(result)
    
    @classmethod
    def parse_file(cls, content: str) -> List[LogLine]:
        """
        Parse entire file content into log lines.
        
        Args:
            content: Full file content
            
        Returns:
            List of parsed LogLine objects
        """
        lines = []
        for raw_line in content.split('\n'):
            if raw_line.strip():
                parsed = cls.parse_line(raw_line)
                if parsed:
                    lines.append(parsed)
        return lines
    
    @classmethod
    def deduplicate(cls, lines: List[LogLine]) -> List[LogLine]:
        """
        Remove duplicate consecutive lines (terminal echo).
        
        Args:
            lines: List of LogLine objects
            
        Returns:
            Deduplicated list
        """
        if not lines:
            return lines
        
        result = [lines[0]]
        for line in lines[1:]:
            # Check if this line is a duplicate of the previous
            prev = result[-1]
            if (line.timestamp == prev.timestamp and 
                line.device_id == prev.device_id and
                line.content == prev.content):
                continue
            result.append(line)
        
        return result
    
    @classmethod
    def extract_commands(cls, lines: List[LogLine], limit: int = 10) -> List[str]:
        """
        Extract recent commands (outgoing lines) from parsed logs.
        
        Args:
            lines: List of LogLine objects
            limit: Maximum number of commands to return
            
        Returns:
            List of command strings
        """
        commands = []
        for line in reversed(lines):
            if line.direction == "out" and line.content:
                commands.append(line.content)
                if len(commands) >= limit:
                    break
        return list(reversed(commands))
