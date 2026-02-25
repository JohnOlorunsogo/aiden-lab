"""Main analyzer that orchestrates error detection and AI analysis."""
import asyncio
import logging
from pathlib import Path
from typing import Callable, List, Optional
from datetime import datetime

from app.core.parser import LogParser
from app.core.detector import error_detector
from app.core.extractor import context_extractor
from app.services.database import db
from app.services.llm import llm_service
from app.models.error import DetectedError, Solution, ErrorWithSolution, Severity, LogLine

logger = logging.getLogger(__name__)


class ErrorAnalyzer:
    """
    Orchestrates the error detection and analysis pipeline.
    
    Flow:
    1. Receives new log content from watcher
    2. Parses and cleans the content
    3. Detects errors using patterns
    4. Extracts context for each error
    5. Sends to Gemini for analysis
    6. Stores results in database
    7. Broadcasts to connected clients
    """
    
    def __init__(self):
        self._broadcast_callbacks: List[Callable] = []
        self._file_lines_cache: dict = {}  # file_path -> List[LogLine]
    
    def register_broadcast(self, callback: Callable):
        """Register a callback to broadcast new errors to clients."""
        self._broadcast_callbacks.append(callback)
        logger.info(f"Registered broadcast callback: {callback}")
    
    async def process_new_content(self, file_path: str, new_content: str):
        """
        Process new content from a log file.
        
        Args:
            file_path: Path to the log file
            new_content: New content appended to the file
        """
        logger.info(f"Processing new content from {file_path} ({len(new_content)} chars)")
        
        # Parse new lines
        new_lines = LogParser.parse_file(new_content)
        
        # If parsing fails, try raw detection
        if not new_lines:
            logger.warning(f"Standard parsing returned no lines, trying raw detection")
            await self._process_raw_content(file_path, new_content)
            return
        
        logger.info(f"Parsed {len(new_lines)} lines from {file_path}")
        
        # Deduplicate
        new_lines = LogParser.deduplicate(new_lines)
        
        # Update cache (append to existing lines)
        if file_path not in self._file_lines_cache:
            self._file_lines_cache[file_path] = []
        self._file_lines_cache[file_path].extend(new_lines)
        
        # Keep only last 1000 lines in cache to prevent memory issues
        if len(self._file_lines_cache[file_path]) > 1000:
            self._file_lines_cache[file_path] = self._file_lines_cache[file_path][-1000:]
        
        # Detect errors in new lines
        errors = error_detector.detect_in_lines(new_lines)
        
        if not errors:
            logger.debug(f"No errors detected in {len(new_lines)} parsed lines")
            return
        
        logger.info(f"Detected {len(errors)} errors in parsed lines")
        
        # Process each error
        for line, severity, pattern in errors:
            await self._process_error(file_path, line, severity, pattern)
    
    async def _process_raw_content(self, file_path: str, content: str):
        """
        Process raw content when structured parsing fails.
        Fallback method for non-standard log formats.
        """
        # Extract device ID from filename
        device_id = Path(file_path).stem
        
        # Detect errors in raw text
        errors = error_detector.detect_raw(content, device_id)
        
        if not errors:
            logger.debug(f"No errors detected in raw content from {file_path}")
            return
        
        logger.info(f"Detected {len(errors)} errors in raw content")
        
        for error_line, severity, pattern in errors:
            await self._process_raw_error(file_path, error_line, severity, pattern, device_id, content)
    
    async def _process_raw_error(
        self,
        file_path: str,
        error_line: str,
        severity: Severity,
        pattern: str,
        device_id: str,
        full_content: str
    ):
        """Process a raw error (unparsed format)."""
        try:
            # Create error object with current timestamp
            detected_error = DetectedError(
                device_id=device_id,
                timestamp=datetime.now(),
                error_line=error_line,
                context=full_content[-500:] if len(full_content) > 500 else full_content,
                severity=severity,
                pattern_matched=pattern
            )
            
            # Store in database
            error_id = await db.insert_error(detected_error)
            detected_error.id = error_id
            
            logger.info(f"Stored raw error {error_id}: {error_line[:50]}...")
            
            # Analyze with LLM (async, non-blocking)
            asyncio.create_task(
                self._analyze_and_store(detected_error, "")
            )
            
            # Broadcast immediately (without waiting for AI)
            await self._broadcast(ErrorWithSolution(error=detected_error, solution=None))
            
        except Exception as e:
            logger.error(f"Error processing raw error: {e}", exc_info=True)
    
    async def _process_error(
        self, 
        file_path: str, 
        error_line: LogLine, 
        severity: Severity,
        pattern: str
    ):
        """Process a single detected error."""
        try:
            # Get all lines for this file from cache
            all_lines = self._file_lines_cache.get(file_path, [])
            
            # Find error index
            error_index = len(all_lines) - 1  # Assume it's the most recent
            for i, line in enumerate(all_lines):
                if line.timestamp == error_line.timestamp and line.content == error_line.content:
                    error_index = i
                    break
            
            # Extract context
            context = context_extractor.extract_from_lines(all_lines, error_index)
            command_history = context_extractor.get_command_history(all_lines, error_index)
            
            # Create error object
            detected_error = DetectedError(
                device_id=error_line.device_id,
                timestamp=error_line.timestamp,
                error_line=error_line.content,
                context=context,
                severity=severity,
                pattern_matched=pattern
            )
            
            # Store in database
            error_id = await db.insert_error(detected_error)
            detected_error.id = error_id
            
            logger.info(f"Stored error {error_id}: {error_line.content[:50]}...")
            
            # Analyze with Gemini (async, non-blocking)
            asyncio.create_task(
                self._analyze_and_store(detected_error, command_history)
            )
            
            # Broadcast immediately (without waiting for AI)
            logger.info(f"Broadcasting error {error_id} to {len(self._broadcast_callbacks)} callbacks")
            await self._broadcast(ErrorWithSolution(error=detected_error, solution=None))
            
        except Exception as e:
            logger.error(f"Error processing error: {e}", exc_info=True)
    
    async def _analyze_and_store(self, error: DetectedError, command_history: str):
        """Analyze error with Gemini and store solution."""
        try:
            # Get AI analysis
            solution = await llm_service.analyze_error(error, command_history)
            solution.error_id = error.id
            
            # Store solution
            solution_id = await db.insert_solution(solution)
            solution.id = solution_id
            
            logger.info(f"Stored solution {solution_id} for error {error.id}")
            
            # Broadcast update with solution
            logger.info(f"Broadcasting solution for error {error.id}")
            await self._broadcast(ErrorWithSolution(error=error, solution=solution))
            
        except Exception as e:
            logger.error(f"Error analyzing with LLM: {e}", exc_info=True)
    
    async def _broadcast(self, error_with_solution: ErrorWithSolution):
        """Broadcast to all registered callbacks."""
        logger.debug(f"Broadcasting to {len(self._broadcast_callbacks)} callbacks")
        
        for callback in self._broadcast_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(error_with_solution)
                else:
                    callback(error_with_solution)
                logger.debug(f"Broadcast successful to {callback}")
            except Exception as e:
                logger.error(f"Broadcast callback error: {e}")
    
    def clear_cache(self):
        """Clear the line cache."""
        self._file_lines_cache.clear()


# Global analyzer instance
error_analyzer = ErrorAnalyzer()
