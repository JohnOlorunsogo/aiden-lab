"""File watcher service using watchdog for real-time log monitoring."""
import asyncio
from pathlib import Path
from typing import Callable, Dict, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import threading
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LogFileHandler(FileSystemEventHandler):
    """Handles file system events for log files."""
    
    def __init__(self, callback: Callable[[str, str], None]):
        """
        Initialize handler.
        
        Args:
            callback: Function to call with (file_path, new_content) when file changes
        """
        super().__init__()
        self._callback = callback
        self._file_positions: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            file_path = event.src_path
            if self._is_log_file(file_path):
                new_content = self._read_new_content(file_path)
                if new_content:
                    self._callback(file_path, new_content)
    
    def _is_log_file(self, file_path: str) -> bool:
        """Check if file is a log file we should monitor."""
        # Accept .log files and files without extension
        path = Path(file_path)
        return path.suffix in ('', '.log', '.txt') and not path.name.startswith('.')
    
    def _read_new_content(self, file_path: str) -> str:
        """Read only new content since last read."""
        with self._lock:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    # Get current position
                    current_pos = self._file_positions.get(file_path, 0)
                    
                    # Seek to last position
                    f.seek(current_pos)
                    
                    # Read new content
                    new_content = f.read()
                    
                    # Update position
                    self._file_positions[file_path] = f.tell()
                    
                    return new_content
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return ""
    
    def reset_position(self, file_path: str):
        """Reset file position to start tracking from beginning."""
        with self._lock:
            self._file_positions[file_path] = 0
    
    def get_tracked_files(self) -> List[str]:
        """Get list of currently tracked files."""
        with self._lock:
            return list(self._file_positions.keys())


class LogWatcher:
    """
    Manages file watching lifecycle for log directory.
    
    Usage:
        watcher = LogWatcher()
        watcher.register_callback(my_handler)
        watcher.start()
        # ... later
        watcher.stop()
    """
    
    def __init__(self, watch_dir: Optional[Path] = None):
        """
        Initialize watcher.
        
        Args:
            watch_dir: Directory to watch (defaults to settings.log_watch_dir)
        """
        self.watch_dir = watch_dir or settings.log_watch_dir
        self._observer: Optional[Observer] = None
        self._handler: Optional[LogFileHandler] = None
        self._callbacks: List[Callable[[str, str], None]] = []
        self._async_callbacks: List[Callable[[str, str], asyncio.coroutine]] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def register_callback(self, callback: Callable[[str, str], None]):
        """
        Register a synchronous callback for new content.
        
        Args:
            callback: Function(file_path, new_content) to call
        """
        self._callbacks.append(callback)
    
    def register_async_callback(self, callback: Callable):
        """
        Register an async callback for new content.
        
        Args:
            callback: Async function(file_path, new_content) to call
        """
        self._async_callbacks.append(callback)
    
    def _dispatch_callbacks(self, file_path: str, new_content: str):
        """Dispatch to all registered callbacks."""
        # Synchronous callbacks
        for callback in self._callbacks:
            try:
                callback(file_path, new_content)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        # Async callbacks - schedule on event loop
        if self._loop and self._async_callbacks:
            for callback in self._async_callbacks:
                try:
                    asyncio.run_coroutine_threadsafe(
                        callback(file_path, new_content),
                        self._loop
                    )
                except Exception as e:
                    logger.error(f"Async callback error: {e}")
    
    def start(self):
        """Start watching the log directory."""
        if self._observer is not None:
            logger.warning("Watcher already running")
            return
        
        # Ensure directory exists
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
        # Create handler and observer
        self._handler = LogFileHandler(self._dispatch_callbacks)
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.watch_dir), recursive=False)
        
        # Try to get current event loop for async callbacks
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        
        self._observer.start()
        logger.info(f"Started watching directory: {self.watch_dir}")
    
    def stop(self):
        """Stop watching the log directory."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            self._handler = None
            logger.info("Stopped watching directory")
    
    def get_watched_files(self) -> List[str]:
        """Get list of files being tracked."""
        if self._handler:
            return self._handler.get_tracked_files()
        return []
    
    @property
    def is_running(self) -> bool:
        """Check if watcher is currently running."""
        return self._observer is not None and self._observer.is_alive()


# Global watcher instance
log_watcher = LogWatcher()
