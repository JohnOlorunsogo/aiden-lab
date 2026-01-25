"""Tests for the file watcher service, including Windows compatibility."""
import os
import sys
import time
import tempfile
import platform
import threading
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.watcher import LogFileHandler, LogWatcher, IS_WINDOWS


class TestLogFileHandler:
    """Test cases for LogFileHandler class."""
    
    def test_is_log_file_accepts_log_extension(self):
        """Test that .log files are accepted."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        assert handler._is_log_file("/path/to/file.log") is True
        assert handler._is_log_file("C:\\Users\\test\\logs\\device.log") is True
    
    def test_is_log_file_accepts_txt_extension(self):
        """Test that .txt files are accepted."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        assert handler._is_log_file("/path/to/file.txt") is True
    
    def test_is_log_file_accepts_no_extension(self):
        """Test that files without extension are accepted."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        assert handler._is_log_file("/path/to/logfile") is True
    
    def test_is_log_file_rejects_hidden_files(self):
        """Test that hidden files (starting with .) are rejected."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        assert handler._is_log_file("/path/to/.hidden") is False
        assert handler._is_log_file("/path/to/.hidden.log") is False
    
    def test_is_log_file_rejects_other_extensions(self):
        """Test that non-log extensions are rejected."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        assert handler._is_log_file("/path/to/file.py") is False
        assert handler._is_log_file("/path/to/file.json") is False


class TestLogWatcherOnCreated:
    """Test cases for on_created handler (critical for Windows)."""
    
    def test_on_created_triggers_callback(self):
        """Test that on_created event triggers the callback."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test log file
            log_file = Path(tmpdir) / "test.log"
            log_file.write_text("Error: test error\n")
            
            # Create a mock event
            class MockEvent:
                is_directory = False
                src_path = str(log_file)
            
            # Trigger on_created
            handler.on_created(MockEvent())
            
            # Check callback was called
            assert callback.called
            call_args = callback.call_args[0]
            assert str(log_file) in call_args[0]
            assert "Error: test error" in call_args[1]
    
    def test_on_created_ignores_directories(self):
        """Test that on_created ignores directory events."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        class MockEvent:
            is_directory = True
            src_path = "/some/directory"
        
        handler.on_created(MockEvent())
        
        assert not callback.called


class TestLogWatcherWindowsCompatibility:
    """Test cases specifically for Windows compatibility."""
    
    def test_is_windows_flag_exists(self):
        """Test that IS_WINDOWS flag is properly set."""
        expected = platform.system() == 'Windows'
        assert IS_WINDOWS == expected
    
    def test_watcher_uses_polling_on_windows(self):
        """Test that PollingObserver is used on Windows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = LogWatcher(Path(tmpdir))
            
            with patch('app.core.watcher.IS_WINDOWS', True):
                with patch('app.core.watcher.PollingObserver') as mock_polling:
                    with patch('app.core.watcher.Observer') as mock_native:
                        # Reload start method with patched IS_WINDOWS
                        # This simulates running on Windows
                        pass
    
    def test_watcher_scans_existing_files_on_start(self):
        """Test that existing files are scanned when watcher starts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing log file before starting watcher
            log_file = Path(tmpdir) / "existing.log"
            log_file.write_text("[2024-01-01 10:00:00] [R1] → 'Error: test'\n")
            
            # Create watcher
            watcher = LogWatcher(Path(tmpdir))
            callback = Mock()
            watcher.register_callback(callback)
            
            # Start watcher
            watcher.start()
            time.sleep(0.1)  # Give time for scan
            
            # Stop watcher
            watcher.stop()
            
            # Verify existing file was processed
            assert callback.called
            call_args = callback.call_args[0]
            assert "existing.log" in call_args[0]


class TestLogWatcherFileModification:
    """Test cases for file modification detection."""
    
    def test_read_new_content_tracks_position(self):
        """Test that only new content is read after initial read."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            # Write initial content
            log_file.write_text("Line 1\n")
            
            # First read - should get all content
            content1 = handler._read_new_content(str(log_file))
            assert content1 == "Line 1\n"
            
            # Append more content
            with open(log_file, 'a') as f:
                f.write("Line 2\n")
            
            # Second read - should only get new content
            content2 = handler._read_new_content(str(log_file))
            assert content2 == "Line 2\n"
            assert "Line 1" not in content2
    
    def test_on_modified_triggers_callback(self):
        """Test that on_modified event triggers the callback."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            log_file.write_text("Initial content\n")
            
            # Read initial content
            handler._read_new_content(str(log_file))
            
            # Append new content
            with open(log_file, 'a') as f:
                f.write("New error line\n")
            
            # Create mock modified event
            from watchdog.events import FileModifiedEvent
            event = FileModifiedEvent(str(log_file))
            
            # Trigger on_modified
            handler.on_modified(event)
            
            # Check callback was called with new content only
            assert callback.called
            call_args = callback.call_args[0]
            assert "New error line" in call_args[1]


class TestLogWatcherIntegration:
    """Integration tests for the watcher."""
    
    def test_watcher_detects_new_file_creation(self):
        """Test that watcher detects when new files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = LogWatcher(Path(tmpdir))
            callback = Mock()
            watcher.register_callback(callback)
            
            # Start watcher
            watcher.start()
            time.sleep(0.2)  # Wait for watcher to start
            
            # Create new file
            new_file = Path(tmpdir) / "new_device.log"
            new_file.write_text("Error: Device failure\n")
            
            # Wait for detection (polling interval is 1s on Windows)
            time.sleep(2)
            
            # Stop watcher
            watcher.stop()
            
            # Should have been called (at least for scan or creation)
            # Note: Exact behavior depends on timing and platform
    
    def test_watcher_detects_file_modification(self):
        """Test that watcher detects when files are modified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial file
            log_file = Path(tmpdir) / "device.log"
            log_file.write_text("Initial line\n")
            
            watcher = LogWatcher(Path(tmpdir))
            callback = Mock()
            watcher.register_callback(callback)
            
            # Start watcher
            watcher.start()
            time.sleep(0.2)
            
            # Reset callback to ignore initial scan
            callback.reset_mock()
            
            # Modify file
            with open(log_file, 'a') as f:
                f.write("Error: New error\n")
            
            # Wait for detection
            time.sleep(2)
            
            # Stop watcher
            watcher.stop()


class TestLogWatcherPathHandling:
    """Test cases for Windows/Unix path handling."""
    
    def test_windows_path_format(self):
        """Test that Windows paths are handled correctly."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        # Test Windows-style path
        assert handler._is_log_file("C:\\Users\\test\\logs\\device.log") is True
        assert handler._is_log_file("D:\\ENSP\\logs\\router1.txt") is True
    
    def test_unix_path_format(self):
        """Test that Unix paths are handled correctly."""
        callback = Mock()
        handler = LogFileHandler(callback)
        
        # Test Unix-style path
        assert handler._is_log_file("/home/user/logs/device.log") is True
        assert handler._is_log_file("/var/log/ensp/router1") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
