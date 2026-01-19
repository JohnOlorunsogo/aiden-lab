"""Tests for the error detector."""
import pytest
from app.core.detector import ErrorDetector
from app.models.error import Severity


class TestErrorDetector:
    """Tests for ErrorDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a fresh detector for each test."""
        return ErrorDetector()
    
    def test_detect_critical_error(self, detector):
        """Test detection of critical error patterns."""
        text = "Error: Failed to connect to peer"
        errors = detector.detect_in_text(text, "test_device")
        
        assert len(errors) == 1
        assert errors[0][1] == Severity.CRITICAL
    
    def test_detect_warning(self, detector):
        """Test detection of warning patterns."""
        text = "Warning: Interface configuration changed"
        errors = detector.detect_in_text(text, "test_device")
        
        assert len(errors) == 1
        assert errors[0][1] == Severity.WARNING
    
    def test_detect_interface_down(self, detector):
        """Test detection of interface down pattern."""
        text = "Interface GigabitEthernet0/0/1 is down"
        errors = detector.detect_in_text(text, "test_device")
        
        assert len(errors) == 1
        assert errors[0][1] == Severity.CRITICAL
    
    def test_detect_unrecognized_command(self, detector):
        """Test detection of unrecognized command."""
        text = "Error: Unrecognized command found at '^' position"
        errors = detector.detect_in_text(text, "test_device")
        
        assert len(errors) == 1
    
    def test_deduplication(self, detector):
        """Test that duplicate errors are not reported."""
        text = "Error: Same error"
        
        # First detection
        errors1 = detector.detect_in_text(text, "test_device")
        assert len(errors1) == 1
        
        # Same error again - should be deduplicated
        errors2 = detector.detect_in_text(text, "test_device")
        assert len(errors2) == 0
    
    def test_no_false_positives(self, detector):
        """Test that normal log lines don't trigger detection."""
        lines = [
            "HUAWEI AR1200 Router",
            "System startup complete",
            "Interface GigabitEthernet0/0/1 is up",
        ]
        
        for line in lines:
            errors = detector.detect_in_text(line, "test")
            assert len(errors) == 0, f"False positive: {line}"
    
    def test_add_custom_pattern(self, detector):
        """Test adding custom patterns."""
        detector.add_pattern(r"CUSTOM_ERROR", Severity.CRITICAL)
        
        errors = detector.detect_in_text("CUSTOM_ERROR occurred", "test")
        assert len(errors) == 1
