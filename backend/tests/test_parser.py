"""Tests for the log parser."""
import pytest
from datetime import datetime
from app.core.parser import LogParser
from app.models.error import LogLine


class TestLogParser:
    """Tests for LogParser class."""
    
    def test_parse_incoming_line(self):
        """Test parsing an incoming log line."""
        raw = "[2026-01-18 03:10:25] [device_2000] ← 'ware, Version 5.130 (AR1200 V200R003C00)\\r'"
        result = LogParser.parse_line(raw)
        
        assert result is not None
        assert result.device_id == "device_2000"
        assert result.direction == "in"
        assert result.timestamp == datetime(2026, 1, 18, 3, 10, 25)
        assert "Version 5.130" in result.content
    
    def test_parse_outgoing_line(self):
        """Test parsing an outgoing log line."""
        raw = "[2026-01-18 03:10:25] [device_2000] → 'display version\\r'"
        result = LogParser.parse_line(raw)
        
        assert result is not None
        assert result.direction == "out"
        assert "display version" in result.content
    
    def test_parse_invalid_line(self):
        """Test that invalid lines are parsed with fallback (flexible parser)."""
        result = LogParser.parse_line("this is not a valid log line")
        # Flexible parser returns a LogLine with 'unknown' device for any content
        assert result is not None
        assert result.device_id == "unknown"
        assert result.direction == "in"
        assert "not a valid" in result.content
    
    def test_clean_content_removes_escapes(self):
        """Test escape sequence removal."""
        # Use actual escape sequence bytes
        content = "\x1b[Adisplay version\r"
        cleaned = LogParser.clean_content(content)
        
        # Should not contain escape sequences
        assert "\x1b" not in cleaned
        assert "\r" not in cleaned
    
    def test_clean_content_removes_doubles(self):
        """Test doubled character removal."""
        content = "ddiissppllaayy"
        cleaned = LogParser.clean_content(content)
        
        assert cleaned == "display"
    
    def test_deduplicate(self):
        """Test line deduplication."""
        lines = [
            LogLine(
                timestamp=datetime(2026, 1, 18, 3, 10, 25),
                device_id="device_2000",
                direction="in",
                content="same content"
            ),
            LogLine(
                timestamp=datetime(2026, 1, 18, 3, 10, 25),
                device_id="device_2000",
                direction="in",
                content="same content"
            ),
            LogLine(
                timestamp=datetime(2026, 1, 18, 3, 10, 26),
                device_id="device_2000",
                direction="in",
                content="different content"
            ),
        ]
        
        result = LogParser.deduplicate(lines)
        assert len(result) == 2
    
    def test_extract_commands(self):
        """Test command extraction."""
        lines = [
            LogLine(timestamp=datetime.now(), device_id="dev", direction="out", content="cmd1"),
            LogLine(timestamp=datetime.now(), device_id="dev", direction="in", content="response"),
            LogLine(timestamp=datetime.now(), device_id="dev", direction="out", content="cmd2"),
        ]
        
        commands = LogParser.extract_commands(lines)
        assert commands == ["cmd1", "cmd2"]
