"""Context extraction for error analysis."""
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from app.config import settings
from app.models.error import LogLine
from app.core.parser import LogParser


class ContextExtractor:
    """Extracts context around detected errors for AI analysis."""
    
    def __init__(self, context_lines: Optional[int] = None):
        """
        Initialize extractor.
        
        Args:
            context_lines: Number of lines of context (default from settings)
        """
        self.context_lines = context_lines or settings.context_lines
    
    def extract_from_lines(
        self, 
        lines: List[LogLine], 
        error_index: int,
        before: Optional[int] = None,
        after: Optional[int] = None
    ) -> str:
        """
        Extract context around an error in a list of lines.
        
        Args:
            lines: List of LogLine objects
            error_index: Index of the error line
            before: Lines before error (default: context_lines // 2)
            after: Lines after error (default: context_lines // 2)
            
        Returns:
            Formatted context string
        """
        before = before if before is not None else self.context_lines // 2
        after = after if after is not None else self.context_lines // 2
        
        start = max(0, error_index - before)
        end = min(len(lines), error_index + after + 1)
        
        context_lines = lines[start:end]
        
        return self._format_lines(context_lines, error_index - start)
    
    def extract_from_file(
        self, 
        file_path: Path, 
        error_line_num: int,
        before: Optional[int] = None,
        after: Optional[int] = None
    ) -> str:
        """
        Extract context from a file around a specific line number.
        
        Args:
            file_path: Path to the log file
            error_line_num: Line number of the error (1-indexed)
            before: Lines before error
            after: Lines after error
            
        Returns:
            Formatted context string
        """
        before = before if before is not None else self.context_lines // 2
        after = after if after is not None else self.context_lines // 2
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
        except Exception as e:
            return f"Error reading file: {e}"
        
        # Convert to 0-indexed
        error_index = error_line_num - 1
        start = max(0, error_index - before)
        end = min(len(all_lines), error_index + after + 1)
        
        raw_lines = all_lines[start:end]
        
        # Parse lines
        parsed_lines = []
        for raw in raw_lines:
            parsed = LogParser.parse_line(raw)
            if parsed:
                parsed_lines.append(parsed)
        
        # Find error in parsed lines
        error_offset = error_index - start
        return self._format_lines(parsed_lines, error_offset)
    
    def extract_from_content(
        self, 
        content: str, 
        error_line: str,
        before: Optional[int] = None,
        after: Optional[int] = None
    ) -> str:
        """
        Extract context from string content around a matching error line.
        
        Args:
            content: Full file content
            error_line: The error line to find
            before: Lines before error
            after: Lines after error
            
        Returns:
            Formatted context string
        """
        before = before if before is not None else self.context_lines // 2
        after = after if after is not None else self.context_lines // 2
        
        all_lines = content.split('\n')
        
        # Find the error line
        error_index = None
        for i, line in enumerate(all_lines):
            if error_line in line:
                error_index = i
                break
        
        if error_index is None:
            # Return last N lines as context
            start = max(0, len(all_lines) - self.context_lines)
            return '\n'.join(all_lines[start:])
        
        start = max(0, error_index - before)
        end = min(len(all_lines), error_index + after + 1)
        
        return '\n'.join(all_lines[start:end])
    
    def _format_lines(self, lines: List[LogLine], error_offset: int) -> str:
        """
        Format context lines for display.
        
        Args:
            lines: List of LogLine objects
            error_offset: Offset of error line in the list
            
        Returns:
            Formatted string with line markers
        """
        result = []
        for i, line in enumerate(lines):
            marker = ">>> " if i == error_offset else "    "
            direction = "<-" if line.direction == "in" else "->"
            formatted = f"{marker}[{line.timestamp.strftime('%H:%M:%S')}] {direction} {line.content}"
            result.append(formatted)
        
        return '\n'.join(result)
    
    def get_command_history(
        self, 
        lines: List[LogLine], 
        error_index: int,
        limit: int = 10
    ) -> str:
        """
        Get recent commands before an error.
        
        Args:
            lines: List of LogLine objects
            error_index: Index of the error
            limit: Max commands to return
            
        Returns:
            Formatted command history
        """
        commands = []
        for i in range(error_index - 1, -1, -1):
            if lines[i].direction == "out":
                commands.append(lines[i].content)
                if len(commands) >= limit:
                    break
        
        if not commands:
            return "No recent commands"
        
        commands.reverse()
        return '\n'.join(f"  {cmd}" for cmd in commands)


# Global extractor instance
context_extractor = ContextExtractor()
